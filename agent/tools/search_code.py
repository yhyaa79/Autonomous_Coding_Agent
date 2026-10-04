from agent.tool_impl import search_code
from agent.tools.base import define_tool

define_tool(
    "search_code",
    "Search text/regex in files (ripgrep if available).",
    {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "path": {"type": "string", "default": "."},
            "glob_pattern": {"type": "string", "default": "*"},
            "case_sensitive": {"type": "boolean", "default": False},
        },
        "required": ["query"],
    },
    lambda a, o: search_code(
        a.get("query", ""),
        a.get("path", "."),
        a.get("glob_pattern", "*"),
        bool(a.get("case_sensitive", False)),
        o,
    ),
)
