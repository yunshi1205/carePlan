import json

from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from care import llm, store


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
