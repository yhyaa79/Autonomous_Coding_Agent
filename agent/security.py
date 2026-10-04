"""کنترل‌های امنیتی برای API و shell."""

import re
from functools import wraps
from typing import Callable

from django.conf import settings
from django.http import HttpRequest, JsonResponse


def project_path_allowed(path: str) -> bool:
    allowlist = getattr(settings, "AGENT_PROJECT_PATH_ALLOWLIST", None) or []
    if not allowlist:
        return True
    resolved = str(path).replace("\\", "/")
    for prefix in allowlist:
        p = str(prefix).replace("\\", "/").rstrip("/")
        if resolved == p or resolved.startswith(p + "/"):
            return True
    return False


_SHELL_BLOCKED: list[re.Pattern[str]] = [
    re.compile(r"rm\s+(-[^\s]*\s+)*-rf\s+(/|\.\.)", re.I),
    re.compile(r"rm\s+-rf\s+/", re.I),
    re.compile(r"\bmkfs\.", re.I),
    re.compile(r":\(\)\s*\{", re.I),
    re.compile(r">\s*/dev/sd[a-z]", re.I),
    re.compile(r"dd\s+if=/dev/zero", re.I),
    re.compile(r"\bcurl\b.+\|\s*sh\b", re.I),
    re.compile(r"\bwget\b.+\|\s*sh\b", re.I),
]


def shell_command_allowed(command: str) -> str | None:
    from agent.store import PRIVATE_DENIED_MESSAGE, command_mentions_private_store

    cmd = (command or "").strip()
    if not cmd:
        return "دستور خالی است"
    if command_mentions_private_store(cmd):
        return PRIVATE_DENIED_MESSAGE
    for pat in _SHELL_BLOCKED:
        if pat.search(cmd):
            return "دستور به‌دلیل خطر امنیتی مسدود شد"
    return None


def require_api_token(view_func: Callable):
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        expected = getattr(settings, "AGENT_API_TOKEN", "") or ""
        if not expected:
            return view_func(request, *args, **kwargs)
        header = request.headers.get("X-ACA-Token") or request.META.get("HTTP_X_ACA_TOKEN")
        if header != expected:
            return JsonResponse({"error": "توکن API نامعتبر است"}, status=401)
        return view_func(request, *args, **kwargs)

    return wrapper
