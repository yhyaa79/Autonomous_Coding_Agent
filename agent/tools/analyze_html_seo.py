from agent.tools._seo_lib import analyze_html_file
from agent.tools.base import define_tool

define_tool(
    "analyze_html_seo",
    "Audit on-page SEO for an HTML/template file in the workspace.",
    {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    },
    lambda a, o: analyze_html_file(a.get("path", ""), o),
)
