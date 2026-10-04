from agent.tool_impl import run_shell
from agent.tools.base import define_tool

define_tool(
    "run_shell",
    "Run shell command with cwd inside workspace.",
    {
        "type": "object",
        "properties": {
            "command": {"type": "string"},
            "cwd": {"type": "string", "default": "."},
        },
        "required": ["command"],
    },
    lambda a, o: run_shell(a.get("command", ""), a.get("cwd", "."), o),
)
