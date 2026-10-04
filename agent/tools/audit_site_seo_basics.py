from agent.tools._seo_lib import audit_site_basics
from agent.tools.base import define_tool

define_tool(
    "audit_site_seo_basics",
    "Check robots.txt, sitemap, list sample HTML paths in project root.",
    {"type": "object", "properties": {}},
    lambda _a, o: audit_site_basics(o),
)
