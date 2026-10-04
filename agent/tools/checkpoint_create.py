from agent.extra_impl import checkpoint_create
from agent.tools.base import define_tool

define_tool(
    "checkpoint_create",
    "Snapshot files before risky edits. The snapshot is stored privately and is not part of the project tree.",
    {
        "type": "object",
        "properties": {
            "paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Files or dirs to copy; default .",
            },
            "label": {"type": "string", "description": "Checkpoint id/label"},
        },
        "required": [],
    },
    lambda a, o: checkpoint_create(a.get("paths") or ["."], a.get("label", ""), o),
)
