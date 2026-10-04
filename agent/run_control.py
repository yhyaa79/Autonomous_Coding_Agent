"""کنترل توقف اجرای هم‌زمان ایجنت برای هر مکالمه."""

from __future__ import annotations

import threading
import uuid
from typing import Dict

_lock = threading.Lock()
_active_run: Dict[int, str] = {}
_cancelled: Dict[str, bool] = {}


def has_active_run(conversation_id: int) -> bool:
    with _lock:
        return int(conversation_id) in _active_run


def try_start_run(conversation_id: int) -> tuple[str | None, bool]:
    """یک run فعال برای هر مکالمه؛ درخواست هم‌زمان دوم رد می‌شود."""
    run_id = uuid.uuid4().hex
    with _lock:
        cid = int(conversation_id)
        if cid in _active_run:
            return None, False
        _active_run[cid] = run_id
        _cancelled[run_id] = False
    return run_id, True


def start_run(conversation_id: int) -> str:
    run_id, ok = try_start_run(conversation_id)
    if not ok:
        raise RuntimeError(f"conversation {conversation_id} already has an active run")
    assert run_id is not None
    return run_id


def end_run(conversation_id: int, run_id: str) -> None:
    with _lock:
        if _active_run.get(int(conversation_id)) == run_id:
            _active_run.pop(int(conversation_id), None)
        _cancelled.pop(run_id, None)


def request_cancel(conversation_id: int, run_id: str) -> bool:
    with _lock:
        if _active_run.get(int(conversation_id)) != run_id:
            return False
        _cancelled[run_id] = True
    _release_blocked_waits(run_id)
    return True


def _release_blocked_waits(run_id: str) -> None:
    """هر انتظار UI (فرم / اجازه) را بیدار کن تا رشتهٔ ایجنت گیر نکند."""
    from agent.permission_gate import cancel_waits_for_run as cancel_perm
    from agent.user_input_gate import cancel_waits_for_run as cancel_input

    cancel_input(run_id)
    cancel_perm(run_id)


def is_cancelled(run_id: str | None) -> bool:
    if not run_id:
        return False
    with _lock:
        return bool(_cancelled.get(run_id))
