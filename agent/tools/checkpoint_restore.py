from agent.extra_impl import checkpoint_restore
from agent.tools.base import define_tool

define_tool(
    "checkpoint_restore",
    "Restore files from a checkpoint id.",
    {
        "type": "object",
        "properties": {"checkpoint_id": {"type": "string"}},
        "required": ["checkpoint_id"],
    },
    lambda a, o: checkpoint_restore(a.get("checkpoint_id", ""), o),
)
