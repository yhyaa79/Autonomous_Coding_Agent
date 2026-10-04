import json
from typing import Any

from .options import AgentOptions
from .registry import ensure_agents_loaded, get_agent
from .tool_impl import tool_result
from .tool_registry import all_tool_definitions, dispatch_registered, tool_definitions_for


def tool_definitions_for_agent(
    agent_type: str | None,
    options: AgentOptions | None = None,
) -> list[dict[str, Any]]:
    ensure_agents_loaded()
    spec = get_agent(agent_type)
    if not spec.tool_definition_ids:
        base = all_tool_definitions()
    else:
        base = tool_definitions_for(spec.tool_definition_ids)

    if not options or not options.project_id:
        return base

    from agent.project_tools.loader import definitions_for_project

    workspace = options.workspace_path()
    extra = definitions_for_project(
        options.project_id,
        workspace,
        options.conversation_id,
    )
    if not extra:
        return base
    seen = {d["function"]["name"] for d in base if d.get("function")}
    merged = list(base)
    for d in extra:
        name = d.get("function", {}).get("name")
        if name and name not in seen:
            merged.append(d)
            seen.add(name)
    return merged


def dispatch_tool(name: str, arguments: dict[str, Any], options: AgentOptions) -> str:
    ensure_agents_loaded()
    if options.project_id:
        from agent.project_tools.loader import dispatch_project_tool

        project_result = dispatch_project_tool(
            options.project_id, name, arguments, options
        )
        if project_result is not None:
            return project_result

    result = dispatch_registered(name, arguments, options)
    if result is not None:
        return result
    hint = ""
    if options.project_id:
        hint = " — در صورت نیاز create_project_tool را برای همین پروژه استفاده کن."
    return tool_result(False, f"Unknown tool: {name}{hint}")


def parse_tool_args(raw: str | None) -> dict[str, Any]:
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
