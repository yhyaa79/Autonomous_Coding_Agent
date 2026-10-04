from agent.tool_impl import read_file
from agent.tools.base import define_tool

define_tool(
    "read_file",
    "Read file with line numbers; use ranges on large files.",
    {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "start_line": {"type": "integer", "default": 1},
            "end_line": {"type": "integer"},
            "max_lines": {"type": "integer", "default": 400},
        },
        "required": ["path"],
    },
    lambda a, o: read_file(
        a.get("path", ""),
        int(a.get("start_line", 1)),
        int(a["end_line"]) if a.get("end_line") is not None else None,
        int(a.get("max_lines", 400)),
        o,
    ),
)
