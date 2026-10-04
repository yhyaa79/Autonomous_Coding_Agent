from agent.extra_impl import web_fetch
from agent.tools.base import define_tool

define_tool(
    "web_fetch",
    "Fetch URL (docs/API). در ایران ممکن است بعضی دامنه‌ها فیلتر باشند — در صورت خطا به کاربر بگو.",
    {
        "type": "object",
        "properties": {"url": {"type": "string"}},
        "required": ["url"],
    },
    lambda a, o: web_fetch(a.get("url", ""), o),
)
