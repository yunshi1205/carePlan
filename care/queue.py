from care.debug_flow import flow


def enqueue_care_plan(careplan_id: int) -> None:
    """Dispatch Celery task — broker stores the job in Redis."""
    from care.tasks import generate_care_plan_task

    generate_care_plan_task.delay(careplan_id)
    flow(
        "S3",
        "queue.enqueue_care_plan — Celery task dispatched",
        careplan_id=careplan_id,
        task="care.generate_care_plan",
    )
