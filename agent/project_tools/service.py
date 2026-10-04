"""ایجاد و مدیریت ابزارهای سفارشی پروژه."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent.options import AgentOptions
from agent.phase_context import emit_phase_event
from agent.phases import phase_event
from agent.tool_create_budget import check_create_project_tool_budget
from agent.tool_impl import tool_result

from .dry_run import dry_run_tool_body
from .loader import invalidate_project_cache, load_project_tool_entries, run_project_tool
from .paths import manifest_path, tool_module_path
from .template import build_module_source
from .validator import (
    ToolValidationError,
    normalize_source_body,
    validate_instagram_publish_body,
    validate_parameters_schema,
    validate_run_body,
    validate_tool_id,
)


def _read_manifest(workspace: Path) -> dict[str, Any]:
    mp = manifest_path(workspace)
    if not mp.is_file():
        return {"version": 1, "tools": []}
    try:
        data = json.loads(mp.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {"version": 1, "tools": []}


def _write_manifest(workspace: Path, data: dict[str, Any]) -> None:
    mp = manifest_path(workspace)
    mp.parent.mkdir(parents=True, exist_ok=True)
    mp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _upsert_manifest_entry(
    workspace: Path,
    tid: str,
    description: str,
    schema: dict[str, Any],
    shared_public_id: str | None = None,
) -> None:
    manifest = _read_manifest(workspace)
    tools = manifest.get("tools")
    if not isinstance(tools, list):
        tools = []
    entry = {
        "id": tid,
        "description": (description or "").strip()[:500],
        "parameters": schema,
    }
    if shared_public_id:
        entry["shared_public_id"] = shared_public_id
    replaced = False
    for i, item in enumerate(tools):
        if isinstance(item, dict) and str(item.get("id") or "") == tid:
            tools[i] = entry
            replaced = True
            break
    if not replaced:
        tools.append(entry)
    manifest["tools"] = tools
    _write_manifest(workspace, manifest)


def create_project_tool(
    tool_id: str,
    description: str,
    parameters: dict[str, Any],
    source_body: str,
    options: AgentOptions,
    test_arguments: dict[str, Any] | None = None,
    replace_existing: bool = False,
) -> str:
    if not options.allow_write:
        return tool_result(False, "Write disabled (allow_write=false)")
    if not options.project_id:
        return tool_result(False, "project_id برای ابزار سفارشی الزامی است")

    budget_err = check_create_project_tool_budget()
    if budget_err:
        return tool_result(False, budget_err)

    emit_phase_event(phase_event("custom_tool_build", f"اعتبارسنجی {tool_id}"))

    source_body = normalize_source_body(source_body)

    try:
        tid = validate_tool_id(tool_id)
        schema = validate_parameters_schema(parameters or {})
        validate_run_body(source_body)
        validate_instagram_publish_body(
            source_body, tid, description, parameters or {}
        )
    except ToolValidationError as e:
        return tool_result(False, str(e))

    workspace = options.workspace_path()
    mod_path = tool_module_path(workspace, tid)
    if mod_path.is_file() and not replace_existing:
        return tool_result(
            False,
            f"ابزار {tid} از قبل وجود دارد — replace_existing:true بفرستید یا tool_id دیگر.",
        )

    emit_phase_event(phase_event("custom_tool_test", f"تست آزمایشی {tid}"))
    try:
        dry_run_tool_body(source_body, test_arguments, options)
    except ToolValidationError as e:
        return tool_result(False, str(e))

    full_source = build_module_source(source_body)
    mod_path.parent.mkdir(parents=True, exist_ok=True)
    emit_phase_event(phase_event("custom_tool_register", f"ثبت {tid}"))
    mod_path.write_text(full_source, encoding="utf-8")

    share_link = ""
    shared_public_id: str | None = None
    register_error = ""
    try:
        from projects.shared_tools import (
            auto_attach_after_create,
            register_shared_tool,
            tool_share_link,
        )

        version = register_shared_tool(
            tool_id=tid,
            display_name=tid,
            description=(description or "").strip(),
            parameters=schema,
            source_body=source_body,
            source_project_id=options.project_id,
            new_version=replace_existing,
            tags=["ops"],
        )
        shared_public_id = version.public_id
        auto_attach_after_create(options, version)
        share_link = tool_share_link(
            version.public_id,
            conversation_id=options.conversation_id,
            project_id=options.project_id,
        )
    except Exception as exc:
        register_error = str(exc)
        share_link = ""

    _upsert_manifest_entry(
        workspace,
        tid,
        description,
        schema,
        shared_public_id=shared_public_id,
    )
    from agent.project_data import upsert_project_tool

    upsert_project_tool(
        project_id=options.project_id,
        tool_id=tid,
        description=description,
        parameters=schema,
        source_body=source_body,
        shared_public_id=shared_public_id or "",
        module_source="",
    )
    invalidate_project_cache(options.project_id, workspace)

    if test_arguments is not None:
        entries = load_project_tool_entries(
            options.project_id, workspace, options.conversation_id
        )
        entry = next((e for e in entries if e.tool_id == tid), None)
        if entry:
            trial = run_project_tool(entry, test_arguments, options)
            if trial.startswith("ERROR:"):
                return tool_result(
                    False,
                    f"ابزار {tid} ثبت شد اما تست مجدد ناموفق: {trial}",
                )
            ok_msg = f"ابزار {tid} ساخته و تست شد.\n{trial}"
            if share_link:
                ok_msg += f"\nلینک منبع (این مکالمه): {share_link}"
            return tool_result(True, ok_msg)

    base_msg = f"ابزار {tid} برای این پروژه ثبت شد. اکنون می‌توانید آن را صدا بزنید."
    if share_link:
        base_msg += f"\nلینک منبع (این مکالمه): {share_link}"
    elif register_error:
        base_msg += f"\n(ثبت منبع در UI ناموفق: {register_error})"
    return tool_result(True, base_msg)


def list_project_tools(options: AgentOptions) -> str:
    if not options.project_id:
        return tool_result(False, "project_id الزامی است")
    entries = load_project_tool_entries(
        options.project_id,
        options.workspace_path(),
        options.conversation_id,
    )
    if not entries:
        return tool_result(True, "(ابزار سفارشی در این مکالمه ثبت نشده)")
    lines = [f"- {e.tool_id}: {e.definition['function']['description']}" for e in entries]
    return tool_result(True, "\n".join(lines))


def test_project_tool(
    tool_id: str,
    arguments: dict[str, Any],
    options: AgentOptions,
) -> str:
    if not options.project_id:
        return tool_result(False, "project_id الزامی است")
    emit_phase_event(phase_event("custom_tool_test", tool_id))
    workspace = options.workspace_path()
    entries = load_project_tool_entries(
        options.project_id, workspace, options.conversation_id
    )
    entry = next((e for e in entries if e.tool_id == tool_id), None)
    if not entry:
        return tool_result(False, f"ابزار {tool_id} پیدا نشد")
    return run_project_tool(entry, arguments or {}, options)
