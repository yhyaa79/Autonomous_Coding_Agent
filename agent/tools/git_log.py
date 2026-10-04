from agent.extra_impl import git_log
from agent.tools.base import define_tool

define_tool(
    "git_log",
    "Recent git commits (oneline).",
    {
        "type": "object",
        "properties": {
            "cwd": {"type": "string", "default": "."},
            "max_count": {"type": "integer", "default": 15},
        },
        "required": [],
    },
    lambda a, o: git_log(o, a.get("cwd", "."), int(a.get("max_count", 15))),
)
