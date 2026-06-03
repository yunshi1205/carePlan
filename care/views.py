import json
import re

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from care import llm, store


def _safe_filename_part(value: str) -> str:
    cleaned = re.sub(r"[^\w\-]", "_", value.strip())
    return cleaned[:50] or "unknown"


def _order_summary(order: dict) -> dict:
    return {
        "id": order["id"],
        "status": order["status"],
        "patient_first_name": order.get("patient_first_name", ""),
        "patient_last_name": order.get("patient_last_name", ""),
        "medication_name": order.get("medication_name", ""),
        "primary_diagnosis": order.get("primary_diagnosis", ""),
        "created_at": order.get("created_at", ""),
    }


def _order_payload(order: dict) -> dict:
    """API response: care_plan only when completed."""
    payload = {
        "id": order["id"],
        "status": order["status"],
        "patient_first_name": order.get("patient_first_name", ""),
        "patient_last_name": order.get("patient_last_name", ""),
        "medication_name": order.get("medication_name", ""),
        "primary_diagnosis": order.get("primary_diagnosis", ""),
    }
    if order["status"] == "completed":
        payload["care_plan"] = order.get("care_plan")
    if order["status"] == "failed":
        payload["error"] = order.get("error")
    return payload


def index(request: HttpRequest):
    return render(request, "care/index.html")


@csrf_exempt
@require_http_methods(["POST"])
def create_order_and_generate(request: HttpRequest):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    fields = {
        "patient_first_name": body.get("patient_first_name", ""),
        "patient_last_name": body.get("patient_last_name", ""),
        "medication_name": body.get("medication_name", ""),
        "primary_diagnosis": body.get("primary_diagnosis", ""),
        "patient_records": body.get("patient_records", ""),
    }

    order = store.create_order(fields)
    order_id = order["id"]

    store.set_status(order_id, "processing")

    try:
        care_plan_text = llm.generate_care_plan(
            patient_first_name=fields["patient_first_name"],
            patient_last_name=fields["patient_last_name"],
            medication_name=fields["medication_name"],
            primary_diagnosis=fields["primary_diagnosis"],
            patient_records=fields["patient_records"],
        )
        order = store.set_status(
            order_id, "completed", care_plan=care_plan_text, error=None
        )
    except Exception as exc:
        order = store.set_status(order_id, "failed", error=str(exc), care_plan=None)

    return JsonResponse(_order_payload(order))


@require_GET
def get_order(request: HttpRequest, order_id: str):
    order = store.get_order(order_id)
    if not order:
        return JsonResponse({"error": "Order not found"}, status=404)
    return JsonResponse(_order_payload(order))


@require_GET
def search_orders(request: HttpRequest):
    query = request.GET.get("q", "")
    orders = store.search_orders(query)
    return JsonResponse({"results": [_order_summary(o) for o in orders]})


@require_GET
def download_care_plan(request: HttpRequest, order_id: str):
    order = store.get_order(order_id)
    if not order:
        return JsonResponse({"error": "Order not found"}, status=404)
    if order["status"] != "completed" or not order.get("care_plan"):
        return JsonResponse(
            {"error": "Care plan is not available until status is completed"},
            status=400,
        )

    last = _safe_filename_part(order.get("patient_last_name", ""))
    med = _safe_filename_part(order.get("medication_name", ""))
    filename = f"care_plan_{last}_{med}.txt"

    response = HttpResponse(
        order["care_plan"],
        content_type="text/plain; charset=utf-8",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
