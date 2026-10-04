"""زمان‌بندی کارهای agent — همان agent اصلی در زمان due اجرا می‌شود."""

import json
from typing import Any

from agent.constants import DEFAULT_AGENT_ID
from agent.options import AgentOptions
from agent.tool_impl import tool_result
from agent.tools._project import require_project_id
from agent.tools.base import define_tool


def _schedule_job(arguments: dict[str, Any], options: AgentOptions) -> str:
    from projects.models import ScheduledJob

    project_id = require_project_id(options)
    title = (arguments.get("title") or "Scheduled task").strip()[:200]
    message = (arguments.get("message") or "").strip()
    if not message:
        return tool_result(False, "message الزامی است")

    schedule_kind = (arguments.get("schedule_kind") or "once").strip()
    valid_kinds = {c[0] for c in ScheduledJob.KIND_CHOICES}
    if schedule_kind not in valid_kinds:
        return tool_result(False, f"schedule_kind نامعتبر: {schedule_kind}")

    from agent.scheduler_service import _parse_run_at

    tz_name = (arguments.get("timezone") or "Asia/Tehran").strip() or "Asia/Tehran"
    run_at_raw = arguments.get("run_at")
    run_at = (
        _parse_run_at(run_at_raw, tz_name)
        if isinstance(run_at_raw, str)
        else run_at_raw
    )

    job = ScheduledJob(
        project_id=project_id,
        source_conversation_id=options.conversation_id,
        created_by_agent_type=DEFAULT_AGENT_ID,
        target_agent_type=DEFAULT_AGENT_ID,
        title=title,
        payload={"message": message, "options": arguments.get("options") or {}},
        schedule_kind=schedule_kind,
        run_at=run_at,
        cron_expression=(arguments.get("cron_expression") or "").strip(),
        interval_seconds=arguments.get("interval_seconds"),
        timezone_name=tz_name,
        max_runs=arguments.get("max_runs"),
    )
    try:
        job.full_clean()
        job.save()
        from agent.scheduler_service import refresh_next_run

        refresh_next_run(job)
        job.save()
    except Exception as exc:
        return tool_result(False, str(exc))

    return tool_result(
        True,
        json.dumps(
            {
                "job_id": job.id,
                "next_run_at": job.next_run_at.isoformat() if job.next_run_at else None,
                "status": job.status,
            },
            ensure_ascii=False,
        ),
    )


define_tool(
    "schedule_job",
    (
        "Schedule a future task for this agent (background worker runs the same agent). "
        "schedule_kind: once | cron | interval. "
        "For once use run_at ISO8601. For cron use cron_expression (5-field). "
        "For interval use interval_seconds."
    ),
    {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "message": {
                "type": "string",
                "description": "دستورالعمل برای agent هنگام اجرا",
            },
            "schedule_kind": {"type": "string"},
            "run_at": {"type": "string"},
            "cron_expression": {"type": "string"},
            "interval_seconds": {"type": "integer"},
            "timezone": {"type": "string"},
            "max_runs": {"type": "integer"},
            "options": {
                "type": "object",
                "description": "allow_shell, allow_write, max_tool_rounds برای اجرا",
            },
        },
        "required": ["title", "message", "schedule_kind"],
    },
    _schedule_job,
)
