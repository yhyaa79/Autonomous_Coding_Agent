from agent.tools._seo_lib import save_seo_report
from agent.tools.base import define_tool

define_tool(
    "save_seo_report",
    "Write a markdown SEO report under seo-reports/ in the workspace.",
    {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "markdown_body": {"type": "string"},
        },
        "required": ["title", "markdown_body"],
    },
    lambda a, o: save_seo_report(a.get("title", "SEO Report"), a.get("markdown_body", ""), o),
)
