from agent.extra_impl import git_commit
from agent.tools.base import define_tool

define_tool(
    "git_commit",
    "git add -A then commit with message (needs allow_write).",
    {
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "cwd": {"type": "string", "default": "."},
        },
        "required": ["message"],
    },
    lambda a, o: git_commit(a.get("message", ""), o, a.get("cwd", ".")),
)
