from agent.tool_impl import project_tree
from agent.tools.base import define_tool

define_tool(
    "project_tree",
    "Compact tree of workspace (respects ignore dirs).",
    {
        "type": "object",
        "properties": {
            "max_depth": {"type": "integer", "default": 3},
            "max_entries": {"type": "integer", "default": 150},
        },
    },
    lambda a, o: project_tree(
        int(a.get("max_depth", 3)),
        int(a.get("max_entries", 150)),
        o,
    ),
)
