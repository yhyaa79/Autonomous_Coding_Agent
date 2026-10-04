"""درخواست اجازه از کاربر در حین اجرای استریم (نوشتن / shell)."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any

_lock = threading.Lock()
_pending: dict[str, _PermissionWait] = {}

WRITE_TOOLS = frozenset(
    {
        "write_file",
        "apply_patch",
        "delete_file",
        "git_commit",
        "checkpoint_create",
        "project_note",
    }
)

SHELL_TOOLS = frozenset({"run_shell"})


@dataclass
class _PermissionWait:
    kind: str
    tool: str
    args: dict[str, Any]
    event: threading.Event
    approved: bool | None = None
    run_id: str | None = None


def tool_needs_write(tool_name: str, args: dict[str, Any] | None = None) -> bool:
    if tool_name in WRITE_TOOLS:
        return True
    if tool_name == "project_note":
        act = (args or {}).get("action") or "append"
        return act in ("append", "write")
    return False


def tool_needs_shell(tool_name: str) -> bool:
    return tool_name in SHELL_TOOLS


def create_permission_request(
    kind: str,
    tool: str,
    args: dict[str, Any],
    *,
    run_id: str | None = None,
) -> str:
    request_id = uuid.uuid4().hex
    with _lock:
        _pending[request_id] = _PermissionWait(
            kind=kind,
            tool=tool,
            args=args,
            event=threading.Event(),
            run_id=run_id,
        )
    return request_id


def resolve_permission(request_id: str, approved: bool) -> bool:
    with _lock:
        wait = _pending.get(request_id)
        if wait is None:
            return False
        wait.approved = bool(approved)
        wait.event.set()
    return True


def wait_permission(
    request_id: str,
    timeout: float | None = None,
    *,
    run_id: str | None = None,
) -> bool | None:
    from django.conf import settings

    from agent.run_control import is_cancelled

    if timeout is None:
        timeout = float(getattr(settings, "AGENT_PERMISSION_TIMEOUT", 600.0))
    with _lock:
        wait = _pending.get(request_id)
    if wait is None:
        return None
    effective_run = run_id or wait.run_id
    deadline = time.monotonic() + max(0.0, float(timeout))
    signaled = False
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        chunk = min(remaining, 1.0)
        if wait.event.wait(timeout=chunk):
            signaled = True
            break
        if effective_run and is_cancelled(effective_run):
            with _lock:
                live = _pending.pop(request_id, None)
            if live is not None:
                live.approved = False
                return False
            return None
    with _lock:
        wait = _pending.pop(request_id, None)
    if not signaled or wait is None:
        return None
    return wait.approved


def cancel_waits_for_run(run_id: str) -> None:
    if not run_id:
        return
    with _lock:
        for request_id, wait in list(_pending.items()):
            if wait.run_id != run_id:
                continue
            wait.approved = False
            wait.event.set()
