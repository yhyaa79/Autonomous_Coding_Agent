import json
from typing import Any

from agent.options import AgentOptions
from agent.tool_impl import tool_result
from agent.tools._project import require_project_id
from agent.tools.base import define_tool


def _list_jobs(arguments: dict[str, Any], options: AgentOptions) -> str:
    from projects.models import ScheduledJob

    project_id = require_project_id(options)
    qs = ScheduledJob.objects.filter(project_id=project_id).order_by("-updated_at")[:30]
    status = arguments.get("status")
    if status:
        qs = qs.filter(status=status)
    items = [
        {
            "id": j.id,
            "title": j.title,
            "schedule_kind": j.schedule_kind,
            "next_run_at": j.next_run_at.isoformat() if j.next_run_at else None,
            "status": j.status,
            "run_count": j.run_count,
        }
        for j in qs
    ]
    return tool_result(True, json.dumps(items, ensure_ascii=False, indent=2))


define_tool(
    "list_scheduled_jobs",
    "List scheduled jobs for current project.",
    {
        "type": "object",
        "properties": {"status": {"type": "string"}},
    },
    _list_jobs,
)
