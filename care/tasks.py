import logging

from celery import shared_task

from care import llm, store
from care.models import CarePlan

logger = logging.getLogger("care.order_flow")

# max_retries=2 → 1 initial attempt + 2 retries = 3 attempts total
MAX_ATTEMPTS = 3


@shared_task(
    bind=True,
    name="care.generate_care_plan",
    max_retries=2,
    default_retry_delay=15,
)
def generate_care_plan_task(self, careplan_id: int) -> None:
    """
    Celery worker task: load CarePlan from DB, call LLM, update status.
    Consumes jobs from Redis via Celery broker (same Redis container).
    """
    attempt = self.request.retries + 1
    logger.info(
        "[CELERY] Task started careplan_id=%s attempt=%s/%s",
        careplan_id,
        attempt,
        MAX_ATTEMPTS,
    )

    try:
        cp = CarePlan.objects.select_related("order", "order__patient").get(
            id=careplan_id
        )
    except CarePlan.DoesNotExist:
        logger.error("[CELERY] CarePlan %s not found — skipping", careplan_id)
        return

    order = cp.order
    store.update_careplan(careplan_id, CarePlan.STATUS_PROCESSING)

    try:
        text = llm.generate_care_plan(
            patient_first_name=order.patient.first_name,
            patient_last_name=order.patient.last_name,
            medication_name=order.medication_name,
            primary_diagnosis=order.primary_diagnosis,
            patient_records=order.patient_records,
        )
        store.update_careplan(
            careplan_id,
            CarePlan.STATUS_COMPLETED,
            content=text,
            error=None,
        )
        logger.info(
            "[CELERY] Task completed careplan_id=%s chars=%s",
            careplan_id,
            len(text),
        )
    except Exception as exc:
        logger.warning(
            "[CELERY] Task failed careplan_id=%s attempt=%s error=%s",
            careplan_id,
            attempt,
            exc,
        )
        if self.request.retries >= self.max_retries:
            store.update_careplan(
                careplan_id,
                CarePlan.STATUS_FAILED,
                content=None,
                error=f"Failed after {MAX_ATTEMPTS} attempts: {exc}",
            )
            logger.error(
                "[CELERY] Task permanently failed careplan_id=%s", careplan_id
            )
            return

        store.update_careplan(
            careplan_id,
            CarePlan.STATUS_PROCESSING,
            error=f"Retry {attempt}/{MAX_ATTEMPTS}: {exc}",
        )
        raise self.retry(exc=exc)
