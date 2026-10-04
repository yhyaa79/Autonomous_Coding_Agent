"""ابزار سفارشی پروژه — توسط ACA ساخته شده."""
from __future__ import annotations

from typing import Any

from agent.options import AgentOptions
from agent.tool_impl import tool_result


def run(arguments: dict[str, Any], options: AgentOptions) -> str:
    def run(arguments):
        text = arguments['text']
        lines = text.splitlines()
        return str(len(lines))
