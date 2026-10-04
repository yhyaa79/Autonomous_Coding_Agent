"""ابزار سفارشی پروژه — توسط ACA ساخته شده."""
from __future__ import annotations

from typing import Any

from agent.options import AgentOptions
from agent.tool_impl import tool_result


def run(arguments: dict[str, Any], options: AgentOptions) -> str:
    from agent.tool_impl import post_instagram_text_story
    username = arguments.get('username')
    password = arguments.get('password')
    story_text = arguments.get('story_text')

    # ارسال استوری به اینستاگرام
    result = post_instagram_text_story(username, password, story_text, {})
    return result
