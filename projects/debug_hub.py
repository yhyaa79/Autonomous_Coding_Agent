"""هاب دیباگ صفحه — تنظیمات پروژه و تاریخچه اسکن."""

from __future__ import annotations

from typing import Any

from django.utils import timezone

from projects.debug_scanner import (
    DEFAULT_CATEGORY_IDS,
    categories_public,
    run_page_debug_scan,
)
from projects.models import DebugScan, ProjectDebugProfile


def get_or_create_profile(project) -> ProjectDebugProfile:
    row, _ = ProjectDebugProfile.objects.get_or_create(
        project=project,
        defaults={
            "last_url": "",
            "preferred_categories": list(DEFAULT_CATEGORY_IDS),
        },
    )
    return row


def scan_to_dict(scan: DebugScan) -> dict[str, Any]:
    return {
        "id": scan.id,
        "url": scan.url,
        "categories": list(scan.categories or []),
        "status": scan.status,
        "findings": list(scan.findings or []),
        "metrics": dict(scan.metrics or {}),
        "summary": dict(scan.summary or {}),
        "error_message": scan.error_message or "",
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
    }


def hub_public_dict(project) -> dict[str, Any]:
    profile = get_or_create_profile(project)
    recent = (
        DebugScan.objects.filter(project=project)
        .order_by("-created_at")[:8]
    )
    latest = recent.first() if recent.exists() else None
    return {
        "last_url": profile.last_url or "",
        "preferred_categories": list(profile.preferred_categories or list(DEFAULT_CATEGORY_IDS)),
        "categories": categories_public(),
        "latest_scan": scan_to_dict(latest) if latest else None,
        "recent_scans": [
            {
                "id": s.id,
                "url": s.url,
                "status": s.status,
                "summary": dict(s.summary or {}),
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in recent
        ],
    }


def apply_profile_patch(profile: ProjectDebugProfile, body: dict[str, Any]) -> tuple[bool, str]:
    if "last_url" in body:
        profile.last_url = str(body.get("last_url") or "").strip()[:500]
    if "preferred_categories" in body:
        raw = body.get("preferred_categories")
        if not isinstance(raw, list):
            return False, "preferred_categories باید آرایه باشد"
        allowed = set(DEFAULT_CATEGORY_IDS)
        profile.preferred_categories = [c for c in raw if c in allowed]
        if not profile.preferred_categories:
            profile.preferred_categories = list(DEFAULT_CATEGORY_IDS)
    profile.save()
    return True, "ذخیره شد"


def execute_scan(project, url: str, categories: list[str] | None) -> DebugScan:
    profile = get_or_create_profile(project)
    target = (url or profile.last_url or "").strip()
    if not target:
        raise ValueError("آدرس صفحه را وارد کنید")
    cats = categories if categories else list(profile.preferred_categories or DEFAULT_CATEGORY_IDS)

    scan = DebugScan.objects.create(
        project=project,
        url=target,
        categories=cats,
        status=DebugScan.STATUS_RUNNING,
    )
    result = run_page_debug_scan(target, cats)
    scan.findings = result.get("findings") or []
    scan.metrics = result.get("metrics") or {}
    scan.summary = result.get("summary") or {}
    scan.error_message = result.get("error") or ""
    scan.status = (
        DebugScan.STATUS_FAILED if not result.get("ok") and result.get("error") else DebugScan.STATUS_COMPLETED
    )
    if not result.get("ok") and not scan.findings:
        scan.status = DebugScan.STATUS_FAILED
    scan.completed_at = timezone.now()
    scan.save()

    if result.get("ok") or scan.url:
        profile.last_url = result.get("url") or target
        profile.save(update_fields=["last_url"])

    return scan
