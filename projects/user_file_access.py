"""دسترسی فایل سراسری کاربر (همهٔ پروژه‌ها)."""

from __future__ import annotations

from agent.scope import normalize_scope_paths

from .models import UserFileAccess


def user_file_access_lists(user) -> tuple[list[str], list[str]]:
    if user is None or not getattr(user, "is_authenticated", False):
        return [], []
    try:
        row = user.file_access
    except UserFileAccess.DoesNotExist:
        return [], []
    always = normalize_scope_paths(row.always_context_paths or [])
    denied = normalize_scope_paths(row.denied_content_paths or [])
    return always, denied


def user_file_access_public(user) -> dict:
    always, denied = user_file_access_lists(user)
    return {
        "always_context_paths": always,
        "denied_content_paths": denied,
    }
