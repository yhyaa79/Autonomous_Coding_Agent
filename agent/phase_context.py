"""جمع‌آوری phase-eventها از داخل ابزارها (مثلاً ساخت tool سفارشی)."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any, Callable

_phase_collector: ContextVar[Callable[[dict[str, Any]], None] | None] = ContextVar(
    "phase_collector", default=None
)


def set_phase_collector(cb: Callable[[dict[str, Any]], None] | None) -> None:
    _phase_collector.set(cb)


def emit_phase_event(event: dict[str, Any]) -> None:
    cb = _phase_collector.get()
    if cb is not None:
        cb(event)
