from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.conf import settings

from .constants import DEFAULT_AGENT_ID, normalize_agent_id
from .scope import normalize_scope_paths


@dataclass
class AgentOptions:
    allow_shell: bool = True
    allow_write: bool = True
    max_tool_rounds: int | None = None
    model: str | None = None
    workspace_root: str | None = None
    scope_paths: list[str] | None = None
    inferred_scope_paths: list[str] | None = None
    scope_note: str = ""
    always_context_paths: list[str] | None = None
    denied_content_paths: list[str] | None = None
    agent_type: str = DEFAULT_AGENT_ID
    project_id: int | None = None
    conversation_id: int | None = None
    enable_thinking: bool = False
    thinking_depth: str = "standard"
    usage_tracker: Any = None
    run_id: str | None = None
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    billing_exempt: bool = False
    remote_session: Any = None
    turn_backup: Any = None

    def workspace_path(self) -> Path:
        if self.workspace_root:
            return Path(self.workspace_root).resolve()
        return Path(settings.AGENT_WORKSPACE).resolve()

    def has_user_scope(self) -> bool:
        """محدودهٔ تعیین‌شده توسط کاربر (مکالمه یا پیش‌فرض پروژه)."""
        return bool(normalize_scope_paths(self.scope_paths))

    def effective_scope(self) -> list[str]:
        """محدودهٔ راهنما برای پرامپت (کاربر یا auto-infer)."""
        user = normalize_scope_paths(self.scope_paths)
        if user:
            return user
        return normalize_scope_paths(self.inferred_scope_paths)

    def enforced_scope(self) -> list[str]:
        """محدودیت محتوای فایل (read/write/patch) — نه اکتشاف ساختار پروژه."""
        return self.content_scope()

    def content_scope(self) -> list[str]:
        """مسیرهایی که محتوای فایل قابل خواندن/ویرایش است؛ خالی = بدون محدودیت."""
        if self.has_user_scope():
            return normalize_scope_paths(self.scope_paths)
        return []

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AgentOptions":
        if not data:
            return cls()
        scope = data.get("scope_paths")
        if scope is not None and not isinstance(scope, list):
            scope = None
        return cls(
            allow_shell=bool(data.get("allow_shell", True)),
            allow_write=bool(data.get("allow_write", True)),
            max_tool_rounds=data.get("max_tool_rounds"),
            model=data.get("model") or None,
            workspace_root=data.get("workspace_root") or None,
            scope_paths=scope,
            scope_note=str(data.get("scope_note") or ""),
            agent_type=normalize_agent_id(str(data.get("agent_type") or DEFAULT_AGENT_ID)),
            project_id=data.get("project_id"),
            conversation_id=data.get("conversation_id"),
            enable_thinking=bool(data.get("enable_thinking", False)),
            thinking_depth=str(data.get("thinking_depth") or "standard"),
        )
