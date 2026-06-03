import copy
import threading
import uuid
from datetime import datetime, timezone
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
        "created_at": datetime.now(timezone.utc).isoformat(),
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


def list_all_orders() -> list[dict[str, Any]]:
    with _lock:
        orders = sorted(
            _orders.values(),
            key=lambda o: o.get("created_at", ""),
            reverse=True,
        )
        return [copy.deepcopy(o) for o in orders]


def search_orders(query: str) -> list[dict[str, Any]]:
    q = query.strip().lower()
    orders = list_all_orders()
    if not q:
        return orders

    results = []
    for order in orders:
        searchable = " ".join(
            [
                order.get("id", ""),
                order.get("patient_first_name", ""),
                order.get("patient_last_name", ""),
                order.get("medication_name", ""),
                order.get("primary_diagnosis", ""),
            ]
        ).lower()
        if q in searchable:
            results.append(order)
    return results
