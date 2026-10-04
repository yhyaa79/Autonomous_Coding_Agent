"""محدودیت تعداد create_project_tool در یک اجرای ایجنت."""

from __future__ import annotations

from contextvars import ContextVar

from django.conf import settings

_attempts: ContextVar[int] = ContextVar("tool_create_attempts", default=0)


def reset_tool_create_budget() -> None:
    _attempts.set(0)


def _max_attempts() -> int:
    return int(getattr(settings, "AGENT_MAX_CREATE_PROJECT_TOOL_ATTEMPTS", 3))


def check_create_project_tool_budget() -> str | None:
    """اگر سقف پر شده باشد پیام خطا برمی‌گرداند."""
    n = _attempts.get()
    if n >= _max_attempts():
        return (
            f"حداکثر {_max_attempts()} بار create_project_tool در این پیام مجاز است. "
            "tool_id جدید نسازید — همان ابزار را با replace_existing:true و source_body اصلاح‌شده "
            "دوباره بفرستید. فایل‌های داخلی ایجنت را با read_file یا apply_patch باز نکنید."
        )
    _attempts.set(n + 1)
    return None
