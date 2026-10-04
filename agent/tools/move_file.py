from agent.extra_impl import move_file
from agent.tools.base import define_tool

define_tool(
    "move_file",
    "Move or rename a file within the workspace.",
    {
        "type": "object",
        "properties": {
            "source": {"type": "string"},
            "destination": {"type": "string"},
        },
        "required": ["source", "destination"],
    },
    lambda a, o: move_file(a.get("source", ""), a.get("destination", ""), o),
)
