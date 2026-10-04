from agent.registry import register_agent
from agent.spec import AgentSpec
from agent.tool_groups import seo_tool_ids

SEO_PROMPT = """You are an **SEO & content agent** for Persian/English sites.

Use analyze_html_seo, audit_site_seo_basics, analyze_content_keywords, save_seo_report.
Read HTML/content via read_file or web_fetch when needed.

Workflow: audit → prioritized fixes → save_seo_report in project.

Rules:
- Respect FOCUS SCOPE for file paths.
- Prefer actionable checklists for the user."""

register_agent(
    AgentSpec(
        id="seo",
        display_name="SEO",
        description="تحلیل SEO، کلمات کلیدی و گزارش در پروژه",
        system_prompt=SEO_PROMPT,
        tool_definition_ids=seo_tool_ids(),
        default_allow_shell=False,
        default_allow_write=True,
        metadata={"stage": "growth", "stage_label": "SEO", "order": 2},
    )
)
