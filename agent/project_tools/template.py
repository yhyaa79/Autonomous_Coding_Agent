"""قالب ماژول ابزار سفارشی."""

from __future__ import annotations

TOOL_TEMPLATE = '''"""ابزار سفارشی پروژه — توسط ACA ساخته شده."""
from __future__ import annotations

from typing import Any

from agent.options import AgentOptions
from agent.tool_impl import tool_result


def run(arguments: dict[str, Any], options: AgentOptions) -> str:
{body}
'''


def indent_body(source: str) -> str:
    lines = source.strip().splitlines()
    if not lines:
        return "    return tool_result(False, 'empty tool')"
    return "\n".join("    " + line if line.strip() else "" for line in lines)


def build_module_source(source_body: str) -> str:
    indented = indent_body(source_body)
    # بدنهٔ کاربر ممکن است { } داشته باشد — از str.format استفاده نکنید.
    return TOOL_TEMPLATE.replace("{body}", indented)
