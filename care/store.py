import copy
import threading
import uuid
from typing import Any

_lock = threading.Lock()
_orders: dict[str, dict[str, Any]] = {}


def create_order(fields: dict[str, Any]) -> dict[str, Any]:
    order_id = str(uuid.uuid4())
    order = {
        "id": order_id,
        "status": "pending",
        "care_plan": None,
        "error": None,
        **fields,
    }
    with _lock:
        _orders[order_id] = order
    return copy.deepcopy(order)


def get_order(order_id: str) -> dict[str, Any] | None:
    with _lock:
        order = _orders.get(order_id)
        return copy.deepcopy(order) if order else None


def set_status(order_id: str, status: str, **extra: Any) -> dict[str, Any] | None:
    with _lock:
        order = _orders.get(order_id)
        if not order:
            return None
        order["status"] = status
        for key, value in extra.items():
            order[key] = value
        return copy.deepcopy(order)
