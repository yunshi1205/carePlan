"""
Trace order generation: frontend console + Docker logs.

Set ORDER_FLOW_BREAKPOINT=1 to pause at numbered steps (pdb / IDE debugger).
"""

import logging
import os

logger = logging.getLogger("care.order_flow")


def _truncate(value, max_len: int = 120) -> str:
    text = str(value)
    if len(text) <= max_len:
        return text
    return f"{text[:max_len]}…({len(text)} chars)"


def flow(step: str, message: str, **context) -> None:
    """Log one step in the order pipeline (always on; see Docker logs)."""
    if context:
        safe = {}
        for key, value in context.items():
            if key == "patient_records" and isinstance(value, str):
                safe[key] = f"<{len(value)} chars>"
            else:
                safe[key] = _truncate(value)
        logger.info("[ORDER_FLOW %s] %s | %s", step, message, safe)
    else:
        logger.info("[ORDER_FLOW %s] %s", step, message)


def flow_break(step: str, message: str, **context) -> None:
    """Log + optional pdb stop when ORDER_FLOW_BREAKPOINT=1."""
    flow(step, message, **context)
    if os.environ.get("ORDER_FLOW_BREAKPOINT") == "1":
        breakpoint()  # noqa: T100
