"""اجرای jobهای زمان‌بندی‌شده — توسط management command یا tick API فراخوانی می‌شود."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)

DEFAULT_TZ = "Asia/Tehran"


def job_timezone(job) -> ZoneInfo:
    name = (getattr(job, "timezone_name", None) or DEFAULT_TZ).strip() or DEFAULT_TZ
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo(DEFAULT_TZ)


def _parse_run_at(value: str | None, tz_name: str | None = None) -> datetime | None:
    if not value:
        return None
    from django.utils.dateparse import parse_datetime

    raw = value.strip()
    dt = parse_datetime(raw)
    if dt is None and len(raw) >= 16:
        dt = parse_datetime(raw.replace(" ", "T"))
    if dt is None:
        return None
    tz = ZoneInfo((tz_name or DEFAULT_TZ).strip() or DEFAULT_TZ)
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, tz)
    return dt.astimezone(tz)


def refresh_next_run(job) -> None:
    """محاسبه next_run_at بر اساس schedule_kind."""
    from projects.models import ScheduledJob

    now = timezone.now()
    tz = job_timezone(job)

    if job.schedule_kind == ScheduledJob.KIND_ONCE:
        if job.run_at:
            run = job.run_at
            if timezone.is_naive(run):
                run = timezone.make_aware(run, tz)
            job.next_run_at = run
        else:
            job.next_run_at = None
        return

    if job.schedule_kind == ScheduledJob.KIND_INTERVAL:
        sec = max(int(job.interval_seconds or 3600), 1)
        if job.last_run_at:
            job.next_run_at = job.last_run_at + timedelta(seconds=sec)
        else:
            job.next_run_at = now
        return

    if job.schedule_kind == ScheduledJob.KIND_CRON:
        try:
            from croniter import croniter
        except ImportError:
            job.next_run_at = now + timedelta(hours=24)
            job.last_error = "croniter not installed"
            return
        expr = (job.cron_expression or "0 9 * * *").strip()
        base = now.astimezone(tz).replace(tzinfo=None)
        itr = croniter(expr, base)
        nxt = itr.get_next(datetime)
        job.next_run_at = timezone.make_aware(nxt, tz)
        return

    job.next_run_at = None


def _due_job_queryset(now, project_id: int | None = None):
    from projects.models import ScheduledJob

    qs = ScheduledJob.objects.filter(status=ScheduledJob.STATUS_ACTIVE)
    if project_id is not None:
        qs = qs.filter(project_id=project_id)
    return qs.filter(
        Q(next_run_at__lte=now)
        | Q(
            next_run_at__isnull=True,
            schedule_kind=ScheduledJob.KIND_ONCE,
            run_at__isnull=False,
            run_at__lte=now,
        )
    )


def execute_job(job_id: int) -> dict[str, Any]:
    from agent.constants import DEFAULT_AGENT_ID, normalize_agent_id
    from agent.loop import run_agent
    from agent.options import AgentOptions
    from projects.models import JobRun, ScheduledJob

    with transaction.atomic():
        job = ScheduledJob.objects.select_for_update().filter(pk=job_id).first()
        if not job or job.status != ScheduledJob.STATUS_ACTIVE:
            return {"ok": False, "reason": "not_active"}

        now = timezone.now()
        if job.next_run_at is None and job.schedule_kind == ScheduledJob.KIND_ONCE:
            refresh_next_run(job)
            job.save(update_fields=["next_run_at", "updated_at"])

        if job.next_run_at and job.next_run_at > now:
            return {"ok": False, "reason": "not_due"}

        payload = job.payload or {}
        message = (payload.get("message") or "").strip()
        extra_opts = payload.get("options") or {}

        from agent.workspace_io import attach_remote_session, close_remote_session
        from projects.remote_server import project_remote_config

        remote_cfg = project_remote_config(job.project)
        workspace_root = remote_cfg.remote_root_path if remote_cfg else job.project.root_path
        from projects.user_file_access import user_file_access_lists

        always_ctx, denied_ctx = user_file_access_lists(job.project.owner)
        opts = AgentOptions(
            allow_shell=bool(extra_opts.get("allow_shell", True)),
            allow_write=bool(extra_opts.get("allow_write", True)),
            max_tool_rounds=extra_opts.get("max_tool_rounds"),
            workspace_root=workspace_root,
            scope_paths=job.project.effective_default_scope(),
            always_context_paths=always_ctx,
            denied_content_paths=denied_ctx,
            agent_type=normalize_agent_id(job.target_agent_type or DEFAULT_AGENT_ID),
            project_id=job.project_id,
            conversation_id=job.source_conversation_id,
        )
        attach_remote_session(opts, remote_cfg)

        run_log = JobRun.objects.create(job=job, status=JobRun.STATUS_RUNNING)

    try:
        prefix = f"[Scheduled job #{job.id} — {job.title}]\n"
        result = run_agent(prefix + message, history=[], options=opts)
        run_log.status = (
            JobRun.STATUS_SUCCESS if not result.get("error") else JobRun.STATUS_FAILED
        )
        run_log.reply = result.get("reply") or ""
        run_log.tool_steps = result.get("tool_steps") or []
        run_log.error_code = result.get("error") or ""
    except Exception as exc:
        logger.exception("job %s failed", job_id)
        run_log.status = JobRun.STATUS_FAILED
        run_log.error_code = "exception"
        run_log.reply = str(exc)
    finally:
        close_remote_session(opts)

    with transaction.atomic():
        job = ScheduledJob.objects.select_for_update().get(pk=job_id)
        job.run_count += 1
        job.last_run_at = timezone.now()
        job.last_error = run_log.error_code or ""

        if job.schedule_kind == ScheduledJob.KIND_ONCE:
            job.status = ScheduledJob.STATUS_COMPLETED
            job.next_run_at = None
        elif job.max_runs and job.run_count >= job.max_runs:
            job.status = ScheduledJob.STATUS_COMPLETED
            job.next_run_at = None
        else:
            refresh_next_run(job)

        job.save()
        run_log.finished_at = timezone.now()
        run_log.save()

    return {
        "ok": True,
        "job_id": job_id,
        "run_id": run_log.id,
        "status": run_log.status,
        "job_title": job.title,
    }


def tick_due_jobs(limit: int = 10, project_id: int | None = None) -> list[dict[str, Any]]:
    now = timezone.now()
    ids = list(
        _due_job_queryset(now, project_id)
        .order_by("next_run_at")
        .values_list("id", flat=True)[:limit]
    )
    results = []
    for jid in ids:
        results.append(execute_job(jid))
    return results


def repair_job_schedules(project_id: int | None = None) -> int:
    """next_run_at خالی برای jobهای فعال را دوباره محاسبه می‌کند."""
    from projects.models import ScheduledJob

    qs = ScheduledJob.objects.filter(status=ScheduledJob.STATUS_ACTIVE)
    if project_id is not None:
        qs = qs.filter(project_id=project_id)
    fixed = 0
    for job in qs:
        if job.next_run_at is None or (
            job.schedule_kind == ScheduledJob.KIND_ONCE and job.run_at
        ):
            refresh_next_run(job)
            job.save(update_fields=["next_run_at", "last_error", "updated_at"])
            fixed += 1
    return fixed
