"""ابزار سفارشی پروژه — توسط ACA ساخته شده."""
from __future__ import annotations

from typing import Any

from agent.options import AgentOptions
from agent.tool_impl import tool_result


def run(arguments: dict[str, Any], options: AgentOptions) -> str:
    path = (arguments.get("path") or "").strip()
    if not path:
        return tool_result(False, "path الزامی است")
    from agent.tool_impl import read_workspace_text
    text = read_workspace_text(path, options)
    if text.startswith("ERROR:"):
        return text
    n = len(text.splitlines())
    return tool_result(True, str(n))
