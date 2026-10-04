"""انتشار استوری اینستاگرام از طریق run_shell / SSH پروژه."""

from agent.options import AgentOptions
from agent.tool_impl import post_instagram_text_story
from agent.tools.base import define_tool


def _instagram_post_story(arguments: dict, options: AgentOptions) -> str:
    return post_instagram_text_story(
        arguments.get("username") or "",
        arguments.get("password") or "",
        arguments.get("story_text") or "",
        options,
    )


define_tool(
    "instagram_post_story",
    "انتشار استوری متنی اینستاگرام (instagrapi روی محیط run_shell — معمولاً سرور SSH پروژه). "
    "رمز را در چت ننویسید؛ از ask_user استفاده کنید. "
    "برای استوری از create_project_tool با return جعلی OK استفاده نکنید.",
    {
        "type": "object",
        "properties": {
            "username": {"type": "string"},
            "password": {"type": "string"},
            "story_text": {"type": "string"},
        },
        "required": ["username", "password", "story_text"],
    },
    _instagram_post_story,
)
