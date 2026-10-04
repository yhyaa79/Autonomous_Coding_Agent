from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class AgentSpec:
    """تعریف یک نوع agent — ابزارها و پرامپت بدون وابستگی به Django view."""

    id: str
    display_name: str
    description: str
    system_prompt: str
    tool_definition_ids: tuple[str, ...] = ()
    default_allow_shell: bool = True
    default_allow_write: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


ToolHandler = Callable[[str, dict[str, Any], Any], str | None]
