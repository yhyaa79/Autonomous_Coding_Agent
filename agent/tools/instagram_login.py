"""ورود اینستاگرام — placeholder تا اتصال رسمی/API اضافه شود."""

import json

from django.utils import timezone

from agent.options import AgentOptions
from agent.project_data import instagram_session_exists, upsert_instagram_session
from agent.tool_impl import tool_result
from agent.tools.base import define_tool


def _instagram_login(arguments: dict, options: AgentOptions) -> str:
    username = (arguments.get("username") or "").strip()
    password = (arguments.get("password") or "").strip()
    if not username:
        return tool_result(False, "username الزامی است")
    if not options.project_id:
        return tool_result(False, "project_id برای ذخیره session الزامی است")

    if not password:
        exists = instagram_session_exists(options.project_id, username)
        return tool_result(
            True,
            json.dumps(
                {
                    "status": "awaiting_password",
                    "existing_session": exists,
                    "note": (
                        "اتصال اینستاگرام هنوز به کتابخانهٔ production وصل نشده. "
                        "با username+password متادیتای session در دیتابیس ذخیره می‌شود "
                        "تا ابزارهای post/publish بعداً از آن استفاده کنند."
                    ),
                },
                ensure_ascii=False,
                indent=2,
            ),
        )

    payload = {
        "username": username,
        "logged_in_at": timezone.now().isoformat(),
    }
    if not upsert_instagram_session(options.project_id, username, payload):
        return tool_result(False, "ذخیره session ناموفق بود")
    return tool_result(
        True,
        json.dumps(
            {
                "status": "session_saved",
                "warning": "این session فعلاً فقط metadata است — قبل از انتشار واقعی API رسمی را پیاده کنید.",
            },
            ensure_ascii=False,
            indent=2,
        ),
    )


define_tool(
    "instagram_login",
    "Save Instagram session metadata in the project database (extend for real API later).",
    {
        "type": "object",
        "properties": {
            "username": {"type": "string"},
            "password": {"type": "string"},
        },
        "required": ["username"],
    },
    _instagram_login,
)
