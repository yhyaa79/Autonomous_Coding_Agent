"""ورود به تلگرام — session در پوشهٔ خصوصی .aca ذخیره می‌شود (نیاز به تنظیم env)."""

import json
import os

from django.conf import settings

from agent.options import AgentOptions
from agent.store import ensure_agent_store, telegram_session_dir
from agent.tool_impl import tool_result
from agent.tools.base import define_tool


def _telegram_login(arguments: dict, options: AgentOptions) -> str:
    api_id = os.environ.get("TELEGRAM_API_ID") or getattr(settings, "TELEGRAM_API_ID", None)
    api_hash = os.environ.get("TELEGRAM_API_HASH") or getattr(settings, "TELEGRAM_API_HASH", None)
    phone = (arguments.get("phone") or "").strip()

    workspace = options.workspace_path()
    ensure_agent_store(workspace)
    session_dir = telegram_session_dir(workspace)
    session_path = session_dir / "user"

    if not api_id or not api_hash:
        return tool_result(
            False,
            "TELEGRAM_API_ID و TELEGRAM_API_HASH در env یا settings تنظیم نشده‌اند. "
            f"مسیر session پیشنهادی: {session_path}",
        )
    if not phone:
        return tool_result(False, "phone الزامی است (با کد کشور، مثلاً +98912...)")

    try:
        from telethon import TelegramClient
        from telethon.errors import SessionPasswordNeededError
    except ImportError:
        return tool_result(
            False,
            "پکیج telethon نصب نیست. pip install telethon سپس دوباره تلاش کنید.",
        )

    code = (arguments.get("code") or "").strip()
    password = (arguments.get("password") or "").strip()

    client = TelegramClient(str(session_path), int(api_id), api_hash)

    async def _flow() -> dict:
        await client.connect()
        if not await client.is_user_authorized():
            if not code:
                await client.send_code_request(phone)
                return {
                    "status": "code_sent",
                    "hint": "کد SMS را با همان phone و فیلد code دوباره schedule_job یا ابزار را صدا بزنید.",
                }
            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                if not password:
                    return {"status": "need_2fa_password", "hint": "password (2FA) را بفرستید."}
                await client.sign_in(password=password)
        me = await client.get_me()
        await client.disconnect()
        return {
            "status": "authorized",
            "user_id": me.id,
            "username": me.username,
            "session_file": str(session_path) + ".session",
        }

    import asyncio

    try:
        payload = asyncio.run(_flow())
    except Exception as exc:
        return tool_result(False, str(exc))

    return tool_result(True, json.dumps(payload, ensure_ascii=False, indent=2))


define_tool(
    "telegram_login",
    (
        "Authenticate Telegram via Telethon. Step 1: phone only → SMS code. "
        "Step 2: phone + code. Step 3 (if 2FA): add password. "
        "Requires TELEGRAM_API_ID / TELEGRAM_API_HASH. Session files live under .aca/sessions/telegram."
    ),
    {
        "type": "object",
        "properties": {
            "phone": {"type": "string"},
            "code": {"type": "string"},
            "password": {"type": "string", "description": "Two-step verification if enabled"},
        },
        "required": ["phone"],
    },
    _telegram_login,
)
