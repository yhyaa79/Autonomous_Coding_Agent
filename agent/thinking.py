"""فاز thinking قبل از حلقهٔ ابزار — برای پروژه‌های بزرگ."""

from typing import Any

from django.conf import settings
from openai import OpenAI

from .options import AgentOptions

THINKING_INSTRUCTION = """کاربر درخواست زیر را داده است. قبل از هر ابکاری، یک تحلیل داخلی بنویس (thinking).

ساختار پاسخ:
1. **هدف کاربر** — یک جمله
2. **فرض‌ها و ابهام‌ها** — اگر چیزی نامشخص است بگو
3. **برنامهٔ کار** — گام‌های مرتب (جستجو در کد → خواندن فایل‌های کلیدی → تغییر کم → تست)
4. **ریسک‌ها** — فایل‌های حساس، breaking change، نیاز به scope
5. **اولین ابزارهای پیشنهادی** — نام ابزار و چرا

قوانین:
- فارسی روان بنویس (کاربر ایرانی است).
- هنوز ابزار اجرا نکن؛ فقط فکر کن.
- اگر پروژه بزرگ است، روی scope و search_code تأکید کن.
- کوتاه ولی کامل (حدود ۱۵۰–۴۰۰ کلمه)."""


def thinking_model(options: AgentOptions) -> str:
    explicit = getattr(settings, "GAPGPT_THINKING_MODEL", "") or ""
    if explicit:
        return explicit
    return options.model or settings.GAPGPT_MODEL


def run_thinking_phase(
    client: OpenAI,
    messages: list[dict[str, Any]],
    user_message: str,
    options: AgentOptions,
) -> str:
    depth = (options.thinking_depth or "standard").strip().lower()
    extra = ""
    if depth == "deep":
        extra = "\nتحلیل عمیق‌تر: وابستگی‌ها، edge caseها، و ترتیب تست را هم بنویس."

    thinking_messages = list(messages)
    thinking_messages.append(
        {
            "role": "user",
            "content": f"{THINKING_INSTRUCTION}{extra}\n\n---\nدرخواست کاربر:\n{user_message}",
        }
    )
    response = client.chat.completions.create(
        model=thinking_model(options),
        messages=thinking_messages,
        temperature=0.35,
    )
    content = (response.choices[0].message.content or "").strip()
    tracker = options.usage_tracker
    if tracker is not None:
        tracker.add_completion(
            thinking_model(options),
            response,
            messages_for_estimate=thinking_messages,
            completion_text=content,
        )
    return content
