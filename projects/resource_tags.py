"""تگ‌های استاندارد کتابخانهٔ منابع — فقط ایجنت منبع می‌سازد."""

from __future__ import annotations

from typing import Any

# id → (برچسب فارسی برای UI, توضیح کوتاه برای ایجنت)
RESOURCE_TAG_CATALOG: dict[str, tuple[str, str]] = {
    "time": (
        "زمان",
        "زمان‌بندی اجرا (once/cron/interval)؛ معمولاً با schedule_job یا فراخوانی منبع دیگر",
    ),
    "connection": (
        "اتصال",
        "SSH، رسانه، API، حساب کاربری — ابتدا تست اتصال، سپس استفاده در دستورات بعدی",
    ),
    "workflow": (
        "گردش‌کار",
        "زنجیرهٔ چند منبع (مثلاً زمان → اتصال → تولید محتوا → انتشار)",
    ),
    "ai": (
        "هوش مصنوعی",
        "جستجو، خلاصه‌سازی، تولید متن/تصویر برای محتوا",
    ),
    "debug": (
        "دیباگ",
        "تحلیل خطا، اسکن صفحه، ابزار عیب‌یابی — جایگزین پنل جداگانه",
    ),
    "ops": (
        "عملیات سرور",
        "nginx، systemd، deploy — معمولاً روی connection SSH ساخته می‌شود",
    ),
    "knowledge": (
        "دانش",
        "متن، راهنما، قوانین برند — بدون اجرای کد",
    ),
}

DEFAULT_RESOURCE_TAGS = frozenset(RESOURCE_TAG_CATALOG.keys())


def normalize_resource_tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    items: list[str] = []
    if isinstance(raw, str):
        items = [p.strip().lower() for p in raw.replace(",", " ").split() if p.strip()]
    elif isinstance(raw, (list, tuple)):
        for item in raw:
            if isinstance(item, str) and item.strip():
                items.append(item.strip().lower())
    out: list[str] = []
    seen: set[str] = set()
    for tag in items:
        if tag in DEFAULT_RESOURCE_TAGS and tag not in seen:
            seen.add(tag)
            out.append(tag)
    return out


def tag_label_fa(tag_id: str) -> str:
    entry = RESOURCE_TAG_CATALOG.get(tag_id)
    return entry[0] if entry else tag_id


def resource_agent_guide_snippet() -> str:
    lines = [
        "## کتابخانهٔ منابع (Resources)",
        "کارهای زمان‌بندی، اتصال به سرور/رسانه، مارکتینگ، دیباگ و عملیات ops را با upsert_knowledge_resource بساز — نه پنل جدا.",
        "همیشه tags مناسب بده: time | connection | workflow | ai | debug | ops | knowledge.",
        "برای اتصال (SSH، اینستا، …): منبع code با test_project_tool؛ اگر credential نداری از کاربر بپرس.",
        "برای زمان‌بندی: منبع با tag time و parameters شامل schedule_kind/run_at/cron؛ body می‌تواند schedule_job را صدا بزند یا منبع دیگر را run کند.",
        "منابع workflow را با parameters.links (لیست tool_id) به هم وصل کن.",
        "بعد از ساخت، منبع به مکالمه وصل می‌شود؛ کاربر فقط توضیحات را در UI می‌خواند.",
    ]
    for tid, (label, hint) in RESOURCE_TAG_CATALOG.items():
        lines.append(f"- {tid} ({label}): {hint}")
    return "\n".join(lines)
