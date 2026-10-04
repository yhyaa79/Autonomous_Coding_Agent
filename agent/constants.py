"""شناسهٔ پیش‌فرض agent."""

DEFAULT_AGENT_ID = "coding"

# نگاشت شناسه‌های قدیمی UI/دیتابیس
LEGACY_AGENT_ALIASES: dict[str, str] = {
    "scheduler": "coding",
    "product": "coding",
    "mentor": "coding",
    "pm": "coding",
    "architect": "coding",
    "qa": "coding",
    "devops": "coding",
}


def normalize_agent_id(agent_id: str | None) -> str:
    raw = (agent_id or DEFAULT_AGENT_ID).strip() or DEFAULT_AGENT_ID
    return LEGACY_AGENT_ALIASES.get(raw, raw)
