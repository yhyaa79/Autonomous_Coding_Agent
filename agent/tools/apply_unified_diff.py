from agent.extra_impl import apply_unified_diff
from agent.tools.base import define_tool

define_tool(
    "apply_unified_diff",
    "Apply unified diff via patch -p1 (needs patch binary on server).",
    {
        "type": "object",
        "properties": {"diff": {"type": "string"}},
        "required": ["diff"],
    },
    lambda a, o: apply_unified_diff(a.get("diff", ""), o),
)
