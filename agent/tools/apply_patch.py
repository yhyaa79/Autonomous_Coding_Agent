from agent.tool_impl import apply_patch
from agent.tools.base import define_tool

define_tool(
    "apply_patch",
    "Replace exactly one occurrence of old_string with new_string.",
    {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "old_string": {"type": "string"},
            "new_string": {"type": "string"},
        },
        "required": ["path", "old_string", "new_string"],
    },
    lambda a, o: apply_patch(
        a.get("path", ""),
        a.get("old_string", ""),
        a.get("new_string", ""),
        o,
    ),
)
