from agent.tool_impl import list_directory
from agent.tools.base import define_tool

define_tool(
    "list_directory",
    "List files/dirs under a relative path.",
    {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "recursive": {"type": "boolean", "default": False},
            "max_entries": {"type": "integer", "default": 200},
        },
        "required": ["path"],
    },
    lambda a, o: list_directory(
        a.get("path", "."),
        bool(a.get("recursive", False)),
        int(a.get("max_entries", 200)),
        o,
    ),
)
