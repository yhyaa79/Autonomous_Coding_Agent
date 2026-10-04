from agent.options import AgentOptions
from agent.tool_impl import tool_result
from agent.tools._project import require_project_id
from agent.tools.base import define_tool


def _cancel_job(arguments: dict, options: AgentOptions) -> str:
    from projects.models import ScheduledJob

    project_id = require_project_id(options)
    job_id = int(arguments.get("job_id") or 0)
    job = ScheduledJob.objects.filter(pk=job_id, project_id=project_id).first()
    if not job:
        return tool_result(False, "job پیدا نشد")
    job.status = ScheduledJob.STATUS_CANCELLED
    job.save(update_fields=["status", "updated_at"])
    return tool_result(True, f"job {job_id} لغو شد")


define_tool(
    "cancel_scheduled_job",
    "Cancel a scheduled job by id.",
    {
        "type": "object",
        "properties": {"job_id": {"type": "integer"}},
        "required": ["job_id"],
    },
    _cancel_job,
)
