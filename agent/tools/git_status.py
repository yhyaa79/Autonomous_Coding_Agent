from agent.extra_impl import git_status
from agent.tools.base import define_tool

define_tool(
    "git_status",
    "Git status (short) in workspace or subfolder.",
    {
        "type": "object",
        "properties": {"cwd": {"type": "string", "default": "."}},
        "required": [],
    },
    lambda a, o: git_status(o, a.get("cwd", ".")),
)
