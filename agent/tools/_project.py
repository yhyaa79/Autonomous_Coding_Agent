"""Context پروژه برای ابزارهای زمان‌بندی."""

from agent.options import AgentOptions


def require_project_id(options: AgentOptions) -> int:
    if not options.project_id:
        raise ValueError("project_id در context agent تنظیم نشده")
    return options.project_id
