"""هاب نگهداری و مارکتینگ پس از استقرار — بازار ایران، کانال‌ها و چک‌لیست."""

from __future__ import annotations

import copy
from typing import Any

from django.utils import timezone

LIFECYCLE_STAGES: tuple[dict[str, str], ...] = (
    {"id": "build", "label": "ساخت", "hint": "توسعه و تست محلی"},
    {"id": "deployed", "label": "استقرار", "hint": "روی سرور / دامنه فعال"},
    {"id": "maintain", "label": "نگهداری", "hint": "پایش، بکاپ، به‌روزرسانی"},
    {"id": "grow", "label": "رشد", "hint": "مارکتینگ و جذب کاربر"},
)

IRAN_CHANNELS: tuple[dict[str, Any], ...] = (
    {
        "id": "telegram",
        "label": "تلگرام",
        "kind": "social",
        "primary": True,
        "notes": "کانال/ربات؛ پراکسی یا API رسمی در صورت دسترسی",
        "fallback_id": "rubika",
    },
    {
        "id": "instagram",
        "label": "اینستاگرام",
        "kind": "social",
        "primary": True,
        "notes": "نیاز به session یا Graph API؛ ممکن است ناپایدار باشد",
        "fallback_id": "telegram",
    },
    {
        "id": "rubika",
        "label": "روبیکا",
        "kind": "social",
        "primary": False,
        "notes": "جایگزین داخلی برای تلگرام در برخی سناریوها",
        "fallback_id": "bale",
    },
    {
        "id": "bale",
        "label": "بله",
        "kind": "social",
        "primary": False,
        "notes": "بات و کانال؛ مخاطب ایرانی",
        "fallback_id": "eitaa",
    },
    {
        "id": "eitaa",
        "label": "ایتا",
        "kind": "social",
        "primary": False,
        "notes": "کانال و گروه",
        "fallback_id": "sms",
    },
    {
        "id": "aparat",
        "label": "آپارات",
        "kind": "video",
        "primary": True,
        "notes": "ویدیو آموزشی / دمو محصول",
        "fallback_id": "",
    },
    {
        "id": "seo_local",
        "label": "SEO داخلی",
        "kind": "seo",
        "primary": True,
        "notes": "گوگل + جستجوی داخلی (ترب، دیجی‌کالا برای محصول فیزیکی)",
        "fallback_id": "",
    },
    {
        "id": "sms",
        "label": "پنل SMS",
        "kind": "direct",
        "primary": False,
        "notes": "کاوه‌نگار، ملی‌پیامک و مشابه — معمولاً دستی/API داخلی",
        "fallback_id": "",
    },
    {
        "id": "word_of_mouth",
        "label": "معرفی شفاهی / B2B",
        "kind": "offline",
        "primary": True,
        "notes": "لینک دعوت، تخفیف معرف، تماس مستقیم",
        "fallback_id": "",
    },
)

DEFAULT_MAINTENANCE_TASKS: tuple[dict[str, str], ...] = (
    {"id": "m_health", "title": "بررسی سلامت سرویس (HTTP/health)", "category": "monitor"},
    {"id": "m_logs", "title": "مرور لاگ خطا و هشدارهای ۵xx", "category": "monitor"},
    {"id": "m_backup", "title": "تأیید بکاپ DB و فایل‌ها", "category": "backup"},
    {"id": "m_ssl", "title": "انقضای SSL / گواهی", "category": "security"},
    {"id": "m_deps", "title": "به‌روزرسانی وابستگی‌های بحرانی", "category": "security"},
    {"id": "m_disk", "title": "فضای دیسک و حافظه سرور", "category": "infra"},
    {"id": "m_secrets", "title": "چرخش کلیدها و env حساس", "category": "security"},
    {"id": "m_uptime_job", "title": "زمان‌بندی پایش خودکار (schedule_job)", "category": "automation"},
)

DEFAULT_MARKETING_TASKS: tuple[dict[str, str], ...] = (
    {"id": "g_positioning", "title": "تعریف ارزش پیشنهادی و مخاطب ایرانی", "category": "strategy"},
    {"id": "g_landing", "title": "بهینه‌سازی لندینگ (فارسی، موبایل، CTA)", "category": "content"},
    {"id": "g_seo_audit", "title": "ممیزی SEO اولیه (ابزار SEO agent)", "category": "seo"},
    {"id": "g_social_bio", "title": "بیو و لینک یکپارچه در شبکه‌های فعال", "category": "social"},
    {"id": "g_content_calendar", "title": "تقویم محتوا ۲ هفته اول", "category": "content"},
    {"id": "g_telegram", "title": "کانال/ربات تلگرام یا جایگزین (روبیکا/بله)", "category": "social"},
    {"id": "g_referral", "title": "طراحی لینک دعوت یا کد تخفیف", "category": "growth"},
    {"id": "g_metrics", "title": "تعریف KPI (ثبت‌نام، فعال، تبدیل)", "category": "analytics"},
)

SUGGESTED_JOBS: tuple[dict[str, Any], ...] = (
    {
        "id": "job_health_daily",
        "title": "پایش روزانه سلامت",
        "target_agent_type": "maintenance",
        "schedule_kind": "cron",
        "cron_expression": "0 8 * * *",
        "message": (
            "پایش نگهداری: آدرس production را از growth hub بخوان؛ web_fetch روی /health یا صفحهٔ اصلی؛ "
            "در صورت SSH فعال، وضعیت سرویس و دیسک را بررسی کن؛ نتیجه را در update_growth_hub ثبت کن."
        ),
    },
    {
        "id": "job_weekly_backup",
        "title": "یادآوری بکاپ هفتگی",
        "target_agent_type": "maintenance",
        "schedule_kind": "cron",
        "cron_expression": "0 9 * * 6",
        "message": "چک‌لیست بکاپ: تأیید آخرین بکاپ DB و فایل؛ در صورت نیاز دستور backup را پیشنهاد بده.",
    },
    {
        "id": "job_social_post",
        "title": "پست هفتگی شبکه اجتماعی",
        "target_agent_type": "marketing",
        "schedule_kind": "cron",
        "cron_expression": "0 10 * * 2",
        "message": (
            "یک پست فارسی کوتاه برای کانال فعال پروژه بنویس (تلگرام/اینستا/روبیکا)؛ "
            "از محدودیت‌های ایران یاد کن؛ در صورت نبود API، متن آمادهٔ کپی برای کاربر بده."
        ),
    },
    {
        "id": "job_seo_monthly",
        "title": "بازبینی ماهانه SEO",
        "target_agent_type": "marketing",
        "schedule_kind": "cron",
        "cron_expression": "0 11 1 * *",
        "message": "audit_site_seo_basics و analyze_content_keywords روی لندینگ؛ save_seo_report و به‌روزرسانی چک‌لیست مارکتینگ.",
    },
)


def _task_template(templates: tuple[dict[str, str], ...]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for t in templates:
        out.append(
            {
                "id": t["id"],
                "title": t["title"],
                "category": t.get("category", ""),
                "done": False,
                "done_at": None,
                "notes": "",
            }
        )
    return out


def default_channels_state() -> dict[str, dict[str, Any]]:
    state: dict[str, dict[str, Any]] = {}
    for ch in IRAN_CHANNELS:
        state[ch["id"]] = {
            "enabled": bool(ch.get("primary")),
            "status": "planned",
            "notes": "",
        }
    return state


def merge_tasks(
    stored: list[dict[str, Any]] | None,
    templates: tuple[dict[str, str], ...],
) -> list[dict[str, Any]]:
    by_id = {t["id"]: t for t in (stored or []) if t.get("id")}
    merged: list[dict[str, Any]] = []
    for tpl in templates:
        tid = tpl["id"]
        row = copy.deepcopy(by_id.get(tid) or {})
        row.setdefault("id", tid)
        row.setdefault("title", tpl["title"])
        row.setdefault("category", tpl.get("category", ""))
        row.setdefault("done", False)
        row.setdefault("done_at", None)
        row.setdefault("notes", "")
        merged.append(row)
    for tid, row in by_id.items():
        if not any(m["id"] == tid for m in merged):
            merged.append(row)
    return merged


def hub_public_dict(hub) -> dict[str, Any]:
    if hub is None:
        return empty_hub_dict()
    return {
        "lifecycle_stage": hub.lifecycle_stage,
        "production_url": hub.production_url or "",
        "launched_at": hub.launched_at.isoformat() if hub.launched_at else None,
        "maintenance_tasks": list(hub.maintenance_tasks or []),
        "marketing_tasks": list(hub.marketing_tasks or []),
        "channels": dict(hub.channels or {}),
        "metrics": dict(hub.metrics or {}),
        "last_maintenance_report": hub.last_maintenance_report or "",
        "last_marketing_plan": hub.last_marketing_plan or "",
        "updated_at": hub.updated_at.isoformat() if hub.updated_at else None,
        "stages": list(LIFECYCLE_STAGES),
        "channel_catalog": list(IRAN_CHANNELS),
        "suggested_jobs": list(SUGGESTED_JOBS),
    }


def empty_hub_dict() -> dict[str, Any]:
    return {
        "lifecycle_stage": "build",
        "production_url": "",
        "launched_at": None,
        "maintenance_tasks": _task_template(DEFAULT_MAINTENANCE_TASKS),
        "marketing_tasks": _task_template(DEFAULT_MARKETING_TASKS),
        "channels": default_channels_state(),
        "metrics": {},
        "last_maintenance_report": "",
        "last_marketing_plan": "",
        "updated_at": None,
        "stages": list(LIFECYCLE_STAGES),
        "channel_catalog": list(IRAN_CHANNELS),
        "suggested_jobs": list(SUGGESTED_JOBS),
    }


def get_or_create_hub(project) -> Any:
    from .models import ProjectGrowthHub

    hub, created = ProjectGrowthHub.objects.get_or_create(project=project)
    if created or not hub.maintenance_tasks:
        hub.maintenance_tasks = merge_tasks(hub.maintenance_tasks, DEFAULT_MAINTENANCE_TASKS)
        hub.marketing_tasks = merge_tasks(hub.marketing_tasks, DEFAULT_MARKETING_TASKS)
        if not hub.channels:
            hub.channels = default_channels_state()
        hub.save()
    else:
        hub.maintenance_tasks = merge_tasks(hub.maintenance_tasks, DEFAULT_MAINTENANCE_TASKS)
        hub.marketing_tasks = merge_tasks(hub.marketing_tasks, DEFAULT_MARKETING_TASKS)
        merged_ch = default_channels_state()
        for k, v in (hub.channels or {}).items():
            if k in merged_ch:
                merged_ch[k].update(v)
        hub.channels = merged_ch
        hub.save(update_fields=["maintenance_tasks", "marketing_tasks", "channels", "updated_at"])
    return hub


def apply_hub_patch(hub, patch: dict[str, Any]) -> tuple[bool, str]:
    from .models import ProjectGrowthHub

    valid_stages = {s["id"] for s in LIFECYCLE_STAGES}
    if "lifecycle_stage" in patch:
        st = str(patch["lifecycle_stage"]).strip()
        if st not in valid_stages:
            return False, f"مرحله نامعتبر: {st}"
        hub.lifecycle_stage = st
        if st in (ProjectGrowthHub.STAGE_DEPLOYED, ProjectGrowthHub.STAGE_MAINTAIN, ProjectGrowthHub.STAGE_GROW):
            if not hub.launched_at:
                hub.launched_at = timezone.now()

    if "production_url" in patch:
        hub.production_url = str(patch["production_url"] or "").strip()[:500]

    if "metrics" in patch and isinstance(patch["metrics"], dict):
        hub.metrics = {**(hub.metrics or {}), **patch["metrics"]}

    if "toggle_task" in patch and isinstance(patch["toggle_task"], dict):
        tt = patch["toggle_task"]
        list_name = tt.get("list")
        task_id = str(tt.get("task_id") or "").strip()
        done = bool(tt.get("done"))
        if list_name == "maintenance":
            hub.maintenance_tasks = _set_task_done(hub.maintenance_tasks, task_id, done)
        elif list_name == "marketing":
            hub.marketing_tasks = _set_task_done(hub.marketing_tasks, task_id, done)
        else:
            return False, "list باید maintenance یا marketing باشد"

    if "channel" in patch and isinstance(patch["channel"], dict):
        ch = patch["channel"]
        cid = str(ch.get("id") or "").strip()
        if cid not in {c["id"] for c in IRAN_CHANNELS}:
            return False, f"کانال نامعتبر: {cid}"
        cur = dict((hub.channels or {}).get(cid) or {})
        if "enabled" in ch:
            cur["enabled"] = bool(ch["enabled"])
        if "status" in ch:
            cur["status"] = str(ch["status"])[:32]
        if "notes" in ch:
            cur["notes"] = str(ch["notes"])[:2000]
        channels = dict(hub.channels or {})
        channels[cid] = cur
        hub.channels = channels

    if "append_report" in patch and isinstance(patch["append_report"], dict):
        ar = patch["append_report"]
        kind = str(ar.get("kind") or "").strip()
        text = str(ar.get("text") or "").strip()
        if not text:
            return False, "متن گزارش خالی است"
        stamp = timezone.now().strftime("%Y-%m-%d %H:%M")
        block = f"\n\n--- {stamp} ---\n{text}\n"
        if kind == "maintenance":
            hub.last_maintenance_report = (hub.last_maintenance_report or "") + block
        elif kind == "marketing":
            hub.last_marketing_plan = (hub.last_marketing_plan or "") + block
        else:
            return False, "kind باید maintenance یا marketing باشد"

    hub.save()
    return True, "ذخیره شد"


def _set_task_done(tasks: list[dict[str, Any]] | None, task_id: str, done: bool) -> list[dict[str, Any]]:
    out = list(tasks or [])
    now = timezone.now().isoformat() if done else None
    found = False
    for row in out:
        if row.get("id") == task_id:
            row["done"] = done
            row["done_at"] = now
            found = True
    if not found and task_id:
        out.append({"id": task_id, "title": task_id, "done": done, "done_at": now, "notes": ""})
    return out


def agent_update_growth_hub(options, arguments: dict[str, Any]) -> str:
    pid = options.project_id
    if not pid:
        return "خطا: project_id در context نیست"

    from projects.models import Project

    project = Project.objects.filter(pk=pid).first()
    if project is None:
        return "پروژه پیدا نشد"
    hub = get_or_create_hub(project)
    ok, msg = apply_hub_patch(hub, arguments)
    if not ok:
        return f"خطا: {msg}"
    return f"OK: {msg} · مرحله={hub.lifecycle_stage} · url={hub.production_url or '—'}"
