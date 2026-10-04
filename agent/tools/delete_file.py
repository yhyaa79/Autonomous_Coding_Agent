from agent.extra_impl import delete_file
from agent.tools.base import define_tool

define_tool(
    "delete_file",
    "Delete a single file (not directories).",
    {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    },
    lambda a, o: delete_file(a.get("path", ""), o),
)
