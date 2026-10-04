from typing import Any


def summarize_tool_steps(tool_steps: list[dict[str, Any]] | None) -> str:
    if not tool_steps:
        return ""
    lines: list[str] = []
    for step in tool_steps:
        name = step.get("tool") or "?"
        result = str(step.get("result") or "")
        if result.startswith("OK:"):
            snippet = result[3:].strip().replace("\n", " ")[:280]
        elif result.startswith("ERROR:"):
            snippet = "خطا: " + result[6:].strip().replace("\n", " ")[:200]
        else:
            snippet = result.replace("\n", " ")[:280]
        args = step.get("args") or {}
        arg_hint = ""
        if isinstance(args, dict):
            for key in ("path", "command", "query", "pattern"):
                if args.get(key):
                    arg_hint = f" ({key}={str(args[key])[:80]})"
                    break
        lines.append(f"- {name}{arg_hint}: {snippet}")
    return "\n".join(lines)


def enrich_assistant_content(content: str, tool_steps: list[dict[str, Any]] | None) -> str:
    summary = summarize_tool_steps(tool_steps)
    body = (content or "").strip()
    if not summary:
        return body
    block = f"[خلاصهٔ ابزارهای این نوبت]\n{summary}"
    if not body:
        return block
    return f"{body}\n\n{block}"


def trim_chat_history(
    history: list[dict[str, Any]],
    max_turns: int,
) -> list[dict[str, Any]]:
    """هر turn = یک جفت user+assistant."""
    if max_turns <= 0 or len(history) <= max_turns * 2:
        return list(history)
    return list(history[-(max_turns * 2) :])


def estimate_text_tokens(text: str) -> int:
    """تخمین سبک برای UI (حدود ۴ کاراکتر به ازای هر توکن)."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def estimate_history_tokens(history: list[dict[str, Any]] | None) -> int:
    total = 0
    for item in history or []:
        role = item.get("role")
        if role in ("user", "assistant"):
            total += estimate_text_tokens(str(item.get("content") or ""))
    return total


def conversation_messages_to_model_history(messages) -> list[dict[str, str]]:
    """تبدیل پیام‌های DB به history قابل ارسال به مدل (با خلاصهٔ tool_steps)."""
    out: list[dict[str, str]] = []
    for m in messages:
        role = m.role
        if role == "user":
            out.append({"role": "user", "content": m.content})
        elif role == "assistant":
            content = enrich_assistant_content(m.content, m.tool_steps or [])
            out.append({"role": "assistant", "content": content})
    return out
