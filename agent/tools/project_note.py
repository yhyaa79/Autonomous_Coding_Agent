from agent.extra_impl import project_note
from agent.tools.base import define_tool

define_tool(
    "project_note",
    "Read/append/write persistent project memory stored for this project.",
    {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["read", "append", "write"]},
            "content": {"type": "string", "default": ""},
        },
        "required": ["action"],
    },
    lambda a, o: project_note(a.get("action", "read"), a.get("content", ""), o),
)
