"""از کاربر در UI فرم بگیر — برای اطلاعات حساس از type=password استفاده کن."""

from agent.tools.base import define_tool

define_tool(
    "ask_user",
    (
        "Ask the user to fill a form in the chat UI. Use when you need credentials, "
        "hostnames, or other data you must not guess. password fields are collected securely. "
        "Never embed secrets in chat text — use this tool instead."
    ),
    {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "عنوان فرم"},
            "message": {"type": "string", "description": "توضیح کوتاه برای کاربر"},
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "type": {
                            "type": "string",
                            "enum": ["text", "password", "multiline"],
                        },
                        "required": {"type": "boolean", "default": True},
                        "placeholder": {"type": "string"},
                    },
                    "required": ["id", "label"],
                },
            },
        },
        "required": ["title", "fields"],
    },
    lambda a, o: "ask_user is handled in agent loop",
)
