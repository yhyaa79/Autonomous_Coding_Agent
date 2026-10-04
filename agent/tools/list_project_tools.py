from agent.project_tools.service import list_project_tools
from agent.tools.base import define_tool

define_tool(
    "list_project_tools",
    "لیست ابزارهای سفارشی ثبت‌شده برای همین پروژه.",
    {"type": "object", "properties": {}, "required": []},
    lambda _a, o: list_project_tools(o),
)
