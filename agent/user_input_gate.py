"""درخواست اطلاعات از کاربر در حین اجرای استریم (فرم با فیلدهای اختیاری/رمز)."""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass
from collections.abc import Iterator
from typing import Any

from agent.tool_impl import tool_result

_lock = threading.Lock()
_pending: dict[str, _UserInputWait] = {}

FIELD_TYPES = frozenset({"text", "password", "multiline"})

DEFAULT_SSH_ASK_FIELDS: list[dict[str, Any]] = [
    {
        "id": "host",
        "label": "آدرس IP یا نام دامنه",
        "type": "text",
        "required": True,
        "placeholder": "مثلاً 203.0.113.10",
    },
    {
        "id": "username",
        "label": "نام کاربری SSH",
        "type": "text",
        "required": True,
        "placeholder": "مثلاً root",
    },
    {
        "id": "password",
        "label": "گذرواژه (در صورت نیاز)",
        "type": "password",
        "required": False,
    },
]


def default_ssh_ask_user_args(message: str = "") -> dict[str, Any]:
    intro = (message or "").strip()
    if len(intro) > 280:
        intro = intro[:277] + "…"
    return {
        "title": "اتصال به سرور",
        "message": intro or "برای اتصال SSH این اطلاعات را وارد کنید.",
        "fields": [dict(f) for f in DEFAULT_SSH_ASK_FIELDS],
    }


def tool_steps_include_ask_user(tool_steps: list[dict[str, Any]]) -> bool:
    return any(s.get("tool") == "ask_user" for s in tool_steps)


def assistant_text_promised_user_form(text: str) -> bool:
    """مدل گفته «فرم»/اطلاعات بدهد ولی ask_user صدا نزده."""
    if not text or len(text.strip()) < 24:
        return False
    raw = text.strip()
    lower = raw.lower()
    cred_hints = (
        "گذرواژه",
        "رمز",
        "password",
        "نام کاربری",
        "username",
        "user name",
        "آدرس ip",
        "ip سرور",
        " ip ",
        "ssh",
        "سرور",
        "nginx",
        "دامنه",
    )
    hits = sum(1 for h in cred_hints if h in raw or h in lower)
    form_hints = (
        "فرم زیر",
        "در فرم",
        "لطفاً این اطلاعات",
        "لطفا این اطلاعات",
        "اطلاعات زیر",
        "وارد کنید",
        "نیاز دارم",
        "form below",
        "fill in the form",
        "fill out",
    )
    has_form_hint = any(h in raw or h in lower for h in form_hints)
    if has_form_hint and hits >= 2:
        return True
    if "1." in raw and "2." in raw and hits >= 2:
        return True
    return False


@dataclass
class _UserInputWait:
    title: str
    message: str
    fields: list[dict[str, Any]]
    event: threading.Event
    response: dict[str, Any] | None = None
    run_id: str | None = None


def _normalize_fields(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or not raw:
        raise ValueError("fields باید آرایه‌ای غیرخالی از فیلدها باشد")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("هر فیلد باید شیء باشد")
        fid = str(item.get("id") or "").strip()
        if not fid or fid in seen:
            raise ValueError("id هر فیلد باید یکتا و غیرخالی باشد")
        seen.add(fid)
        ftype = str(item.get("type") or "text").strip().lower()
        if ftype not in FIELD_TYPES:
            raise ValueError(f"type نامعتبر برای فیلد {fid}")
        label = str(item.get("label") or fid).strip()
        required = bool(item.get("required", True))
        placeholder = str(item.get("placeholder") or "").strip()
        out.append(
            {
                "id": fid,
                "label": label,
                "type": ftype,
                "required": required,
                "placeholder": placeholder,
            }
        )
    return out


def password_field_ids(fields: list[dict[str, Any]]) -> frozenset[str]:
    return frozenset(
        f["id"] for f in fields if str(f.get("type") or "").lower() == "password"
    )


def redact_ask_user_step(step: dict[str, Any]) -> dict[str, Any]:
    """حذف مقادیر حساس از trace ذخیره‌شده / UI."""
    if step.get("tool") != "ask_user":
        return step
    args = step.get("args") or {}
    fields = args.get("fields") if isinstance(args.get("fields"), list) else []
    secret_ids = password_field_ids(fields)
    if not secret_ids:
        return step
    out = dict(step)
    result = out.get("result")
    if isinstance(result, str) and result.strip():
        try:
            prefix = ""
            body = result
            if result.startswith("OK:") or result.startswith("ERROR:"):
                prefix, body = result.split(":", 1)
                prefix = prefix + ":"
                body = body.lstrip()
            data = json.loads(body) if body.strip().startswith("{") else None
            if isinstance(data, dict) and isinstance(data.get("values"), dict):
                values = dict(data["values"])
                for sid in secret_ids:
                    if sid in values:
                        values[sid] = "••••••••"
                data["values"] = values
                new_payload = json.dumps(data, ensure_ascii=False, indent=2)
                out["result"] = f"{prefix} {new_payload}".strip() if prefix else new_payload
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return out


def create_user_input_request(
    title: str,
    message: str,
    fields: list[dict[str, Any]],
    *,
    run_id: str | None = None,
) -> str:
    request_id = uuid.uuid4().hex
    with _lock:
        _pending[request_id] = _UserInputWait(
            title=title,
            message=message,
            fields=fields,
            event=threading.Event(),
            run_id=run_id,
        )
    return request_id


def resolve_user_input(request_id: str, payload: dict[str, Any] | None) -> bool:
    with _lock:
        wait = _pending.get(request_id)
        if wait is None:
            return False
        wait.response = payload if payload is not None else {"cancelled": True}
        wait.event.set()
    return True


def wait_user_input(
    request_id: str,
    timeout: float | None = None,
    *,
    run_id: str | None = None,
) -> dict[str, Any] | None:
    from django.conf import settings

    from agent.run_control import is_cancelled

    if timeout is None:
        timeout = float(getattr(settings, "AGENT_USER_INPUT_TIMEOUT", 1800.0))
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
                return {"cancelled": True}
            return None
    with _lock:
        wait = _pending.pop(request_id, None)
    if not signaled or wait is None:
        return None
    return wait.response


def cancel_waits_for_run(run_id: str) -> None:
    if not run_id:
        return
    with _lock:
        for request_id, wait in list(_pending.items()):
            if wait.run_id != run_id:
                continue
            wait.response = {"cancelled": True}
            wait.event.set()


def iter_ask_user(
    arguments: dict[str, Any],
    *,
    run_id: str | None = None,
) -> Iterator[dict[str, Any]]:
    """رویدادهای SSE را یکی‌یکی yield می‌کند؛ نتیجهٔ ابزار در return (StopIteration.value)."""
    title = str(arguments.get("title") or "ورود اطلاعات").strip() or "ورود اطلاعات"
    message = str(arguments.get("message") or "").strip()
    try:
        fields = _normalize_fields(arguments.get("fields"))
    except ValueError as exc:
        return tool_result(False, str(exc))

    request_id = create_user_input_request(title, message, fields, run_id=run_id)
    yield {
        "type": "user_input_request",
        "request_id": request_id,
        "title": title,
        "message": message,
        "fields": fields,
    }
    response = wait_user_input(request_id, run_id=run_id)
    if response is None:
        yield {
            "type": "user_input_resolved",
            "request_id": request_id,
            "cancelled": True,
            "timed_out": True,
        }
        return tool_result(False, "زمان پاسخ کاربر تمام شد.")

    if response.get("cancelled"):
        yield {
            "type": "user_input_resolved",
            "request_id": request_id,
            "cancelled": True,
        }
        return tool_result(False, "کاربر ورود اطلاعات را لغو کرد.")

    values_in = response.get("values") if isinstance(response.get("values"), dict) else {}
    notes = str(response.get("notes") or "").strip()
    values_out: dict[str, str] = {}
    missing: list[str] = []
    for f in fields:
        fid = f["id"]
        raw = values_in.get(fid)
        val = str(raw).strip() if raw is not None else ""
        if f.get("required") and not val:
            missing.append(f.get("label") or fid)
            continue
        values_out[fid] = val
    if missing:
        yield {
            "type": "user_input_resolved",
            "request_id": request_id,
            "cancelled": True,
            "validation_error": True,
        }
        return tool_result(
            False,
            "فیلدهای الزامی خالی بودند: " + "، ".join(missing),
        )

    payload = {"values": values_out}
    if notes:
        payload["notes"] = notes
    yield {
        "type": "user_input_resolved",
        "request_id": request_id,
        "cancelled": False,
    }
    return tool_result(True, json.dumps(payload, ensure_ascii=False, indent=2))


def execute_ask_user(arguments: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    """جمع‌آوری همهٔ رویدادها (برای تست و فراخوانی غیراستریم)."""
    events: list[dict[str, Any]] = []
    gen = iter_ask_user(arguments)
    try:
        while True:
            events.append(next(gen))
    except StopIteration as stop:
        return events, stop.value
