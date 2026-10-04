from agent.project_tools.service import create_project_tool
from agent.tools.base import define_tool

_TOOL_BODY_EXAMPLE = (
    'path = (arguments.get("path") or "").strip()\\n'
    "if not path:\\n"
    '    return tool_result(False, "path الزامی است")\\n'
    "from agent.tool_impl import read_workspace_text\\n"
    "text = read_workspace_text(path, options)\\n"
    'if text.startswith("ERROR:"):\\n'
    "    return text\\n"
    "n = len(text.splitlines())\\n"
    'return tool_result(True, str(n))'
)

define_tool(
    "create_project_tool",
    "ساخت ابزار سفارشی؛ ورژن جدید در کتابخانهٔ منابع و اتصال به مکالمه. "
    "قبل از نوشتن فایل، کد تست می‌شود. حداکثر چند بار در هر پیام — tool_id جدید نسازید؛ "
    "با replace_existing:true همان tool_id را اصلاح کنید. "
    "source_body = بدنهٔ run (return tool_result؛ try/except مجاز). ورودی ابزار: arguments.get(...) "
    "— نه parameters (همان نام فیلد JSON است). اگر def run() گذاشتید خودکار باز می‌شود؛ "
    "importها را قبل def run یا ابتدای بدنه بنویسید. "
    "فایل: read_workspace_text / write_workspace_text(path, content, options) از agent.tool_impl — open() مجاز نیست. "
    f"نمونهٔ شمارش خطوط فایل: {_TOOL_BODY_EXAMPLE} "
    "اینستاگرام/استوری: ابزار instagram_post_story را صدا بزنید یا در source_body "
    "post_instagram_text_story(username, password, story_text, options) از agent.tool_impl — "
    "return tool_result(True,'استوری ارسال شد') بدون انتشار واقعی رد می‌شود.",
    {
        "type": "object",
        "properties": {
            "tool_id": {"type": "string"},
            "description": {"type": "string"},
            "parameters": {"type": "object"},
            "source_body": {
                "type": "string",
                "description": "کد داخل run — return tool_result(True/False, ...)",
            },
            "test_arguments": {"type": "object"},
            "replace_existing": {
                "type": "boolean",
                "description": "اگر ابزار با همین tool_id وجود دارد، ورژن code جدید بساز",
            },
        },
        "required": ["tool_id", "description", "parameters", "source_body"],
    },
    lambda a, o: create_project_tool(
        a.get("tool_id", ""),
        a.get("description", ""),
        a.get("parameters") or {},
        a.get("source_body", ""),
        o,
        a.get("test_arguments"),
        bool(a.get("replace_existing")),
    ),
)
