from typing import Any

from .options import AgentOptions
from .spec import ToolHandler

_TOOL_DEFS: dict[str, dict[str, Any]] = {}
_TOOL_HANDLERS: dict[str, ToolHandler] = {}


def register_tool(
    tool_id: str,
    definition: dict[str, Any],
    handler: ToolHandler,
) -> None:
    fn = definition.get("function") or {}
    name = fn.get("name") or tool_id
    if name != tool_id:
        raise ValueError(f"tool id {tool_id} must match function.name {name}")
    _TOOL_DEFS[tool_id] = definition
    _TOOL_HANDLERS[tool_id] = handler


def tool_definitions_for(ids: tuple[str, ...]) -> list[dict[str, Any]]:
    missing = [i for i in ids if i not in _TOOL_DEFS]
    if missing:
        raise KeyError(f"Unknown tools: {missing}")
    return [_TOOL_DEFS[i] for i in ids]


def dispatch_registered(
    name: str,
    arguments: dict[str, Any],
    options: AgentOptions,
) -> str | None:
    handler = _TOOL_HANDLERS.get(name)
    if handler is None:
        return None
    return handler(name, arguments, options)


def all_tool_ids() -> tuple[str, ...]:
    return tuple(sorted(_TOOL_DEFS.keys()))


def all_tool_definitions() -> list[dict[str, Any]]:
    return [_TOOL_DEFS[i] for i in sorted(_TOOL_DEFS.keys())]
