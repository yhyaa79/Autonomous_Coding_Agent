from agent.registry import register_agent
from agent.spec import AgentSpec
from agent.tool_groups import social_tool_ids

SOCIAL_PROMPT = """You help with **Telegram / Instagram** session setup and scheduled posts (Iranian users).

Use telegram_login / instagram_login for session metadata; **instagram_post_story** for real story publish (via project SSH + instagrapi on server). Never fake success with create_project_tool stubs.
Read project_note for account hints the user saved.

Rules:
- Never ask for passwords in chat logs; use env credentials.
- Explain when API keys (TELEGRAM_API_ID, etc.) are missing."""

register_agent(
    AgentSpec(
        id="social",
        display_name="شبکه‌های اجتماعی",
        description="تلگرام، اینستاگرام و زمان‌بندی",
        system_prompt=SOCIAL_PROMPT,
        tool_definition_ids=social_tool_ids(),
        default_allow_shell=False,
        default_allow_write=False,
        metadata={"stage": "social", "stage_label": "اجتماعی", "order": 3},
    )
)
