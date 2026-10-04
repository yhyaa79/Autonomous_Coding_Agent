from typing import Any

from .constants import DEFAULT_AGENT_ID, normalize_agent_id
from .spec import AgentSpec

_AGENTS: dict[str, AgentSpec] = {}


def register_agent(spec: AgentSpec) -> None:
    if spec.id in _AGENTS:
        raise ValueError(f"Duplicate agent id: {spec.id}")
    _AGENTS[spec.id] = spec


def get_agent(agent_id: str | None) -> AgentSpec:
    aid = normalize_agent_id(agent_id)
    if aid in _AGENTS:
        return _AGENTS[aid]
    if DEFAULT_AGENT_ID in _AGENTS:
        return _AGENTS[DEFAULT_AGENT_ID]
    return next(iter(_AGENTS.values()))


def list_agents() -> list[dict[str, Any]]:
    items = [
        {
            "id": s.id,
            "display_name": s.display_name,
            "description": s.description,
            "default_allow_shell": s.default_allow_shell,
            "default_allow_write": s.default_allow_write,
            "stage": (s.metadata or {}).get("stage", "build"),
            "stage_label": (s.metadata or {}).get("stage_label", ""),
            "order": int((s.metadata or {}).get("order", 99)),
        }
        for s in _AGENTS.values()
    ]
    items.sort(key=lambda x: (x["order"], x["display_name"]))
    return items


def valid_agent_ids() -> set[str]:
    ensure_agents_loaded()
    from .constants import LEGACY_AGENT_ALIASES

    ids = set(_AGENTS.keys())
    ids.update(LEGACY_AGENT_ALIASES.keys())
    return ids


def ensure_agents_loaded() -> None:
    from .tools import ensure_tools_loaded
    from . import agents as _agents  # noqa: F401

    ensure_tools_loaded()
    _ = _agents
