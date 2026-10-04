from agent.knowledge_resources import upsert_knowledge_resource
from agent.tools.base import define_tool

define_tool(
    "upsert_knowledge_resource",
    "ثبت یا ورژن جدید منبع در کتابخانه (متن، اتصال، زمان، کد اجرایی). tags: time, connection, workflow, ai, debug, ops, knowledge.",
    {
        "type": "object",
        "properties": {
            "tool_id": {"type": "string", "description": "شناسهٔ ثابت منبع (slug)"},
            "display_name": {
                "type": "string",
                "description": "فقط هنگام ساخت اول — بعداً تغییر نمی‌کند",
            },
            "description": {"type": "string"},
            "content_kind": {
                "type": "string",
                "enum": ["prompt", "code", "link", "image", "video", "audio", "mixed"],
            },
            "content_blocks": {
                "type": "array",
                "description": "بلوک‌های {type,text|url,label,caption}",
            },
            "source_body": {
                "type": "string",
                "description": "بدنهٔ run برای منابع code",
            },
            "parameters": {"type": "object"},
            "new_version": {
                "type": "boolean",
                "description": "اگر منبع وجود دارد، ورژن جدید بساز",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "time | connection | workflow | ai | debug | ops | knowledge",
            },
        },
        "required": ["tool_id", "description"],
    },
    lambda a, o: upsert_knowledge_resource(
        str(a.get("tool_id") or ""),
        str(a.get("description") or ""),
        str(a.get("content_kind") or "prompt"),
        a.get("content_blocks") if isinstance(a.get("content_blocks"), list) else None,
        str(a.get("source_body") or ""),
        a.get("parameters") if isinstance(a.get("parameters"), dict) else {},
        str(a.get("display_name") or ""),
        bool(a.get("new_version")),
        a.get("tags") if isinstance(a.get("tags"), list) else None,
        o,
    ),
)
