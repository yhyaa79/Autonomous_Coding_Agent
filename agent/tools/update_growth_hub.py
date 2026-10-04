from agent.tools.base import define_tool
from projects.growth_hub import agent_update_growth_hub

define_tool(
    "update_growth_hub",
    (
        "به‌روزرسانی هاب نگهداری/مارکتینگ پروژه: مرحلهٔ چرخه، URL تولید، چک‌لیست، کانال‌های ایران، گزارش."
    ),
    {
        "type": "object",
        "properties": {
            "lifecycle_stage": {
                "type": "string",
                "enum": ["build", "deployed", "maintain", "grow"],
                "description": "مرحلهٔ چرخه عمر محصول",
            },
            "production_url": {"type": "string", "description": "آدرس عمومی سرویس (https://…)"},
            "toggle_task": {
                "type": "object",
                "properties": {
                    "list": {"type": "string", "enum": ["maintenance", "marketing"]},
                    "task_id": {"type": "string"},
                    "done": {"type": "boolean"},
                },
            },
            "channel": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "enabled": {"type": "boolean"},
                    "status": {
                        "type": "string",
                        "description": "planned|active|paused|blocked",
                    },
                    "notes": {"type": "string"},
                },
            },
            "append_report": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "enum": ["maintenance", "marketing"]},
                    "text": {"type": "string"},
                },
            },
            "metrics": {
                "type": "object",
                "description": "KPIهای ساده مثل signups، mau",
            },
        },
    },
    lambda a, o: agent_update_growth_hub(o, a),
)
