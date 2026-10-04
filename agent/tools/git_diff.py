from agent.extra_impl import git_diff
from agent.tools.base import define_tool

define_tool(
    "git_diff",
    "Git diff (unstaged or --staged).",
    {
        "type": "object",
        "properties": {
            "cwd": {"type": "string", "default": "."},
            "staged": {"type": "boolean", "default": False},
        },
        "required": [],
    },
    lambda a, o: git_diff(o, a.get("cwd", "."), bool(a.get("staged"))),
)
