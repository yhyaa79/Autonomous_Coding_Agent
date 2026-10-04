from agent.tools._seo_lib import analyze_content_seo
from agent.tools.base import define_tool

define_tool(
    "analyze_content_keywords",
    "Keyword density and heading sample for a content/HTML file.",
    {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "keywords": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["path", "keywords"],
    },
    lambda a, o: analyze_content_seo(a.get("path", ""), list(a.get("keywords") or []), o),
)
