from agent.project_tools.service import test_project_tool
from agent.tools.base import define_tool

define_tool(
    "test_project_tool",
    "تست یک ابزار سفارشی همین پروژه با arguments.",
    {
        "type": "object",
        "properties": {
            "tool_id": {"type": "string"},
            "arguments": {"type": "object"},
        },
        "required": ["tool_id"],
    },
    lambda a, o: test_project_tool(a.get("tool_id", ""), a.get("arguments") or {}, o),
)
