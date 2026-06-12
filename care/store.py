import random
import uuid
from typing import Any

from django.db.models import Q

from care.debug_flow import flow, flow_break
from care.models import CarePlan, Order, Patient, Provider


DEFAULT_PROVIDER_NPI = "1000000001"
DEFAULT_PROVIDER_NAME = "Default Provider"


def _order_to_dict(order: Order) -> dict[str, Any]:
    cp = order.care_plan
    return {
        "id": str(order.id),
        "careplan_id": cp.id,
        "status": cp.status,
        "care_plan": cp.content if cp.status == CarePlan.STATUS_COMPLETED else None,
        "error": cp.error if cp.status == CarePlan.STATUS_FAILED else None,
        "patient_first_name": order.patient.first_name,
        "patient_last_name": order.patient.last_name,
        "medication_name": order.medication_name,
        "primary_diagnosis": order.primary_diagnosis,
        "patient_records": order.patient_records,
        "created_at": order.created_at.isoformat(),
    }


def _next_ephemeral_mrn() -> str:
    """Unique 6-digit MRN for orders created via the web form (no MRN field yet)."""
    for _ in range(100):
        candidate = f"{random.randint(0, 999999):06d}"
        if not Patient.objects.filter(mrn=candidate).exists():
            return candidate
    return str(uuid.uuid4().int)[-6:]


def _default_provider() -> Provider:
    provider, _ = Provider.objects.get_or_create(
        npi=DEFAULT_PROVIDER_NPI,
        defaults={"name": DEFAULT_PROVIDER_NAME},
    )
    return provider


def create_order(fields: dict[str, Any]) -> dict[str, Any]:
    patient = Patient.objects.create(
        first_name=fields.get("patient_first_name", ""),
        last_name=fields.get("patient_last_name", ""),
        mrn=_next_ephemeral_mrn(),
        date_of_birth=None,
    )
    provider = _default_provider()
    order = Order.objects.create(
        patient=patient,
        provider=provider,
        medication_name=fields.get("medication_name", ""),
        primary_diagnosis=fields.get("primary_diagnosis", ""),
        additional_diagnoses=fields.get("additional_diagnoses") or [],
        medication_history=fields.get("medication_history") or [],
        patient_records=fields.get("patient_records", ""),
    )
    CarePlan.objects.create(order=order, status=CarePlan.STATUS_PENDING)

    order_id = str(order.id)
    flow_break(
        "S1",
        "store.create_order — saved to PostgreSQL",
        order_id=order_id,
        status="pending",
        medication=fields.get("medication_name", ""),
    )
    return _order_to_dict(order)


def create_order_and_enqueue(fields: dict[str, Any]) -> dict[str, Any]:
    """Create order + pending CarePlan, then dispatch Celery task."""
    from care.queue import enqueue_care_plan

    order_dict = create_order(fields)
    careplan_id = order_dict["careplan_id"]
    enqueue_care_plan(careplan_id)
    return order_dict


def update_careplan(careplan_id: int, status: str, **extra: Any) -> None:
    cp = CarePlan.objects.get(id=careplan_id)
    cp.status = status
    if "content" in extra:
        cp.content = extra["content"]
    if "error" in extra:
        cp.error = extra["error"]
    cp.save()
    flow(
        "S2",
        "store.update_careplan — updated in PostgreSQL",
        careplan_id=careplan_id,
        status=status,
        has_content=bool(cp.content),
        has_error=bool(cp.error),
    )


def get_order(order_id: str) -> dict[str, Any] | None:
    try:
        order = Order.objects.select_related("patient", "care_plan").get(id=order_id)
    except Order.DoesNotExist:
        return None
    return _order_to_dict(order)


def set_status(order_id: str, status: str, **extra: Any) -> dict[str, Any] | None:
    try:
        order = Order.objects.select_related("patient", "care_plan").get(id=order_id)
    except Order.DoesNotExist:
        return None

    cp = order.care_plan
    cp.status = status
    if "care_plan" in extra:
        cp.content = extra["care_plan"]
    if "error" in extra:
        cp.error = extra["error"]
    cp.save()

    flow(
        "S2",
        "store.set_status — updated in PostgreSQL",
        order_id=order_id,
        status=status,
        has_care_plan=bool(cp.content),
        has_error=bool(cp.error),
    )
    return _order_to_dict(order)


def list_all_orders() -> list[dict[str, Any]]:
    orders = Order.objects.select_related("patient", "care_plan").all()
    return [_order_to_dict(o) for o in orders]


def search_orders(query: str) -> list[dict[str, Any]]:
    q = query.strip()
    qs = Order.objects.select_related("patient", "care_plan").all()
    if q:
        qs = qs.filter(
            Q(id__icontains=q)
            | Q(patient__first_name__icontains=q)
            | Q(patient__last_name__icontains=q)
            | Q(medication_name__icontains=q)
            | Q(primary_diagnosis__icontains=q)
        )
    return [_order_to_dict(o) for o in qs]
