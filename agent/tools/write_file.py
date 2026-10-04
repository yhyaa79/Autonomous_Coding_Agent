from agent.tool_impl import write_file
from agent.tools.base import define_tool

define_tool(
    "write_file",
    "Create or overwrite a file. Prefer apply_patch for edits.",
    {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    },
    lambda a, o: write_file(a.get("path", ""), a.get("content", ""), o),
)
