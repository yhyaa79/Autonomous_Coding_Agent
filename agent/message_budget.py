"""کوتاه‌کردن history و payload قبل از فراخوانی chat.completions — جلوگیری از 400 upstream."""

from __future__ import annotations

import copy
import json
from typing import Any

from django.conf import settings

from agent.model_catalog import model_context_window

# فیلدهای ابزار که اغلب کل فایل را در arguments می‌گذارند
_TOOL_ARG_TEXT_KEYS = (
    "old_string",
    "new_string",
    "content",
    "command",
    "query",
    "pattern",
    "message",
)


def _int_setting(name: str, default: int) -> int:
    return int(getattr(settings, name, default))


def truncate_tool_arguments_json(raw: str | None, *, max_field: int | None = None) -> str:
    cap = max_field or _int_setting("AGENT_MAX_TOOL_ARG_FIELD_CHARS", 600)
    raw = raw or "{}"
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        if len(raw) <= cap * 2:
            return raw
        return raw[: cap * 2] + "...(truncated)"
    if not isinstance(obj, dict):
        return raw[: cap * 2] if len(raw) > cap * 2 else raw
    changed = False
    for key in _TOOL_ARG_TEXT_KEYS:
        val = obj.get(key)
        if isinstance(val, str) and len(val) > cap:
            obj[key] = val[:cap] + "...(truncated in API history)"
            changed = True
    if not changed:
        return raw
    return json.dumps(obj, ensure_ascii=False)


def trim_text_content(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    head = max_len // 2
    tail = max_len - head - 40
    if tail < 0:
        return text[:max_len] + "...(truncated)"
    return text[:head] + "\n...(truncated)...\n" + text[-tail:]


def trim_history_message_content(content: str) -> str:
    max_len = _int_setting("AGENT_MAX_HISTORY_MESSAGE_CHARS", 6000)
    text = (content or "").strip()
    marker = "[خلاصهٔ ابزارهای این نوبت]"
    if marker in text:
        body, _, summary = text.partition(marker)
        body = body.strip()
        summary_block = marker + summary
        summary_cap = min(2500, max_len // 2)
        if len(summary_block) > summary_cap:
            summary_block = summary_block[:summary_cap] + "\n...(tool summary truncated)"
        room = max(500, max_len - len(summary_block) - 20)
        if len(body) > room:
            body = trim_text_content(body, room)
        return f"{body}\n\n{summary_block}" if body else summary_block
    return trim_text_content(text, max_len)


def _sanitize_one_message(msg: dict[str, Any], *, aggressive: bool) -> dict[str, Any]:
    out = copy.deepcopy(msg)
    role = out.get("role")
    max_content = _int_setting("AGENT_MAX_TOOL_RESULT_CHARS", 8000)
    if aggressive:
        max_content = min(max_content, 4000)
    content = out.get("content")
    if isinstance(content, str):
        out["content"] = trim_text_content(content, max_content)
    elif content is None and role == "assistant" and out.get("tool_calls"):
        out["content"] = None

    tool_calls = out.get("tool_calls")
    if isinstance(tool_calls, list):
        arg_cap = 400 if aggressive else None
        for tc in tool_calls:
            if not isinstance(tc, dict):
                continue
            fn = tc.get("function")
            if not isinstance(fn, dict):
                continue
            fn["arguments"] = truncate_tool_arguments_json(
                fn.get("arguments"), max_field=arg_cap
            )
    return out


def _message_char_weight(msg: dict[str, Any]) -> int:
    total = 0
    c = msg.get("content")
    if isinstance(c, str):
        total += len(c)
    tool_calls = msg.get("tool_calls")
    if tool_calls:
        total += len(json.dumps(tool_calls, ensure_ascii=False))
    return total


def _payload_char_cap(model: str, *, aggressive: bool) -> int:
    explicit = _int_setting("AGENT_MAX_CHAT_PAYLOAD_CHARS", 0)
    if explicit > 0:
        cap = explicit
    else:
        tokens = model_context_window(model)
        # ~۳.۵ char/token؛ سقف محافظه‌کار برای proxy/upstream
        cap = min(int(tokens * 3.5), 220_000)
    if aggressive:
        cap = min(cap, 80_000)
    return cap


def prepare_messages_for_chat_completion(
    messages: list[dict[str, Any]],
    model: str,
    *,
    aggressive: bool = False,
) -> list[dict[str, Any]]:
    """پیام‌ها را برای API ایمن و کوتاه می‌کند (بدون تغییر لیست اصلی caller)."""
    if not messages:
        return []
    sanitized = [_sanitize_one_message(m, aggressive=aggressive) for m in messages]
    cap = _payload_char_cap(model, aggressive=aggressive)
    total = sum(_message_char_weight(m) for m in sanitized)
    if total <= cap:
        return sanitized

    # system اول را نگه دار؛ از وسط history حذف کن
    if len(sanitized) <= 3:
        return sanitized

    head = sanitized[:2]
    tail = sanitized[2:]
    while tail and sum(_message_char_weight(m) for m in head + tail) > cap:
        if len(tail) <= 2:
            # آخرین user + context assistant/tool را فشار بده
            last = tail.pop()
            if isinstance(last.get("content"), str):
                last["content"] = trim_text_content(
                    last["content"],
                    2000 if aggressive else 4000,
                )
            tail.append(last)
            break
        tail.pop(0)
    return head + tail


def assistant_tool_message_for_api(message: Any) -> dict[str, Any]:
    """نسخهٔ assistant با tool_calls برای history همان دور (arguments کوتاه)."""
    data = message.model_dump(exclude_none=True)
    tool_calls = data.get("tool_calls")
    if isinstance(tool_calls, list):
        for tc in tool_calls:
            if not isinstance(tc, dict):
                continue
            fn = tc.get("function")
            if isinstance(fn, dict):
                fn["arguments"] = truncate_tool_arguments_json(fn.get("arguments"))
    if data.get("content") in ("", None) and tool_calls:
        data["content"] = None
    return data
