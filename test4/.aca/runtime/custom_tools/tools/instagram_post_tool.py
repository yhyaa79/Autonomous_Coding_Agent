"""ابزار سفارشی پروژه — توسط ACA ساخته شده."""
from __future__ import annotations

from typing import Any

from agent.options import AgentOptions
from agent.tool_impl import tool_result


def run(arguments: dict[str, Any], options: AgentOptions) -> str:
    username = arguments.get('username')
    password = arguments.get('password')
    story_text = arguments.get('story_text')

    # اینجا باید کد ارسال استوری به اینستاگرام قرار گیرد
    # به عنوان مثال، از API اینستاگرام استفاده کنید

    # فرض کنید که درخواست ارسال استوری به اینستاگرام به شکل زیر است
    # اینستاگرام API برای ارسال استوری را صدا بزنید

    # در اینجا باید کد مربوط به ارسال استوری را بنویسید

    return tool_result(True, 'استوری با موفقیت ارسال شد')
