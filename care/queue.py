import redis
from django.conf import settings

QUEUE_KEY = "careplan:queue"


def _client() -> redis.Redis:
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=int(settings.REDIS_PORT),
        db=int(settings.REDIS_DB),
        decode_responses=True,
    )


def enqueue_care_plan(careplan_id: int) -> None:
    """Push careplan_id onto Redis list (worker will consume later)."""
    _client().lpush(QUEUE_KEY, str(careplan_id))
