"""برچسب مراحل اجرا برای UI (فارسی)."""

from typing import Any

# id → (label_fa, توضیح کوتاه)
PHASE_LABELS: dict[str, str] = {
    "receive": "دریافت پیام",
    "thinking": "فاز thinking (تحلیل)",
    "focus_auto": "تشخیص خودکار محدودهٔ focus",
    "model_plan": "برنامه‌ریزی و انتخاب ابزار",
    "compose": "نوشتن پاسخ نهایی",
    "done": "پایان",
    "custom_tool_build": "ساخت ابزار سفارشی (اعتبارسنجی)",
    "custom_tool_register": "ثبت ابزار در پروژه",
    "custom_tool_test": "تست ابزار سفارشی",
    "debug_analyze": "دیباگ — تحلیل خطا",
    "debug_strategy": "دیباگ — راه‌حل جایگزین",
    "debug_escalate": "دیباگ — ارجاع به کاربر",
}

TOOL_PHASES: dict[str, tuple[str, str]] = {
    "read_file": ("read", "خواندن فایل"),
    "project_tree": ("explore", "بررسی ساختار پروژه"),
    "list_directory": ("explore", "لیست پوشه"),
    "glob_files": ("explore", "جستجوی فایل"),
    "search_code": ("search", "جستجو در کد"),
    "write_file": ("write", "نوشتن فایل"),
    "apply_patch": ("write", "ویرایش فایل (patch)"),
    "apply_unified_diff": ("write", "اعمال diff"),
    "delete_file": ("write", "حذف فایل"),
    "move_file": ("write", "جابجایی فایل"),
    "run_shell": ("shell", "اجرای shell"),
    "run_tests": ("test", "اجرای تست"),
    "format_lint": ("lint", "lint / format"),
    "git_status": ("git", "وضعیت git"),
    "git_diff": ("git", "diff گیت"),
    "git_log": ("git", "تاریخچه git"),
    "git_commit": ("git", "commit گیت"),
    "web_fetch": ("fetch", "دریافت از وب"),
    "project_note": ("memory", "یادداشت پروژه"),
    "checkpoint_create": ("checkpoint", "ایجاد checkpoint"),
    "checkpoint_restore": ("checkpoint", "بازگردانی checkpoint"),
    "schedule_job": ("schedule", "زمان‌بندی"),
    "list_scheduled_jobs": ("schedule", "لیست jobها"),
    "cancel_scheduled_job": ("schedule", "لغو job"),
    "analyze_html_seo": ("seo", "تحلیل SEO"),
    "audit_site_seo_basics": ("seo", "ممیزی SEO"),
    "analyze_content_keywords": ("seo", "کلمات کلیدی"),
    "save_seo_report": ("seo", "ذخیره گزارش SEO"),
    "telegram_login": ("social", "ورود تلگرام"),
    "instagram_login": ("social", "ورود اینستاگرام"),
    "instagram_post_story": ("social", "انتشار استوری اینستاگرام"),
    "update_growth_hub": ("growth", "هاب نگهداری/مارکتینگ"),
    "create_project_tool": ("custom_tool", "ساخت ابزار پروژه"),
    "list_project_tools": ("custom_tool", "لیست ابزارهای پروژه"),
    "test_project_tool": ("custom_tool", "تست ابزار پروژه"),
}


def phase_event(phase_id: str, detail: str = "", **extra: Any) -> dict[str, Any]:
    label = PHASE_LABELS.get(phase_id, phase_id)
    return {
        "type": "phase",
        "phase": phase_id,
        "label": label,
        "detail": detail,
        **extra,
    }


def phase_for_tool(tool_name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    args = args or {}
    stage_id, label = TOOL_PHASES.get(tool_name, ("tool", f"ابزار: {tool_name}"))
    detail = ""
    for key in ("path", "command", "url", "query", "pattern", "source"):
        if args.get(key):
            detail = str(args[key])[:120]
            break
    return {
        "type": "phase",
        "phase": stage_id,
        "label": label,
        "detail": detail,
        "tool": tool_name,
    }
