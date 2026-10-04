from agent.tool_impl import glob_files
from agent.tools.base import define_tool

define_tool(
    "glob_files",
    "Find files by glob (e.g. **/*.py).",
    {
        "type": "object",
        "properties": {
            "pattern": {"type": "string"},
            "path": {"type": "string", "default": "."},
        },
        "required": ["pattern"],
    },
    lambda a, o: glob_files(a.get("pattern", "*"), a.get("path", "."), o),
)
