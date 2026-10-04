"""ابزار سفارشی پروژه — توسط ACA ساخته شده."""
from __future__ import annotations

from typing import Any

from agent.options import AgentOptions
from agent.tool_impl import tool_result


def run(arguments: dict[str, Any], options: AgentOptions) -> str:
    text = arguments.get("text")
    if not text:
        return tool_result(False, "text الزامی است")

    # تبدیل متن به slug
    slug = text.lower().replace(' ','-').replace('،','').replace('(','').replace(')','').replace('vs','vs')
    return tool_result(True, slug)
