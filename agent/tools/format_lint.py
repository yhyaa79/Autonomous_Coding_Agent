from agent.extra_impl import format_lint
from agent.tools.base import define_tool

define_tool(
    "format_lint",
    "Run ruff / ruff_format / eslint on path.",
    {
        "type": "object",
        "properties": {
            "tool": {
                "type": "string",
                "enum": ["ruff", "ruff_format", "eslint"],
                "default": "ruff",
            },
            "path": {"type": "string", "default": "."},
        },
        "required": [],
    },
    lambda a, o: format_lint(a.get("tool", "ruff"), a.get("path", "."), o),
)
