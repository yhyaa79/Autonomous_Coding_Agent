"""بارگذاری ابزارهای سفارشی. سورس در دیتابیس است و فایل اجرا داخل .aca ساخته می‌شود."""

from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent.options import AgentOptions
from agent.tool_impl import tool_result

from agent.project_tools.template import build_module_source
from agent.store import ensure_agent_store

from .paths import TOOLS_DIR, manifest_path, tool_module_path


@dataclass
class ProjectToolEntry:
    tool_id: str
    definition: dict[str, Any]
    module_path: Path


_CACHE: dict[tuple[int, str], tuple[float, list[ProjectToolEntry]]] = {}


def _load_manifest(workspace: Path) -> list[dict[str, Any]]:
    mp = manifest_path(workspace)
    if not mp.is_file():
        return []
    try:
        data = json.loads(mp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    tools = data.get("tools")
    return tools if isinstance(tools, list) else []


def _mtime_key(workspace: Path) -> float:
    mp = manifest_path(workspace)
    if not mp.is_file():
        return 0.0
    try:
        t = mp.stat().st_mtime
        for p in (workspace / TOOLS_DIR).glob("*.py"):
            t = max(t, p.stat().st_mtime)
        return t
    except OSError:
        return mp.stat().st_mtime


def _materialize_module(workspace: Path, tool_id: str, source_body: str, module_source: str) -> Path:
    ensure_agent_store(workspace)
    mod = tool_module_path(workspace, tool_id)
    text = module_source.strip() and module_source or build_module_source(source_body)
    if not mod.is_file() or mod.read_text(encoding="utf-8") != text:
        mod.parent.mkdir(parents=True, exist_ok=True)
        mod.write_text(text, encoding="utf-8")
    return mod


def _entries_from_db(project_id: int, workspace: Path) -> list[tuple[str, dict[str, Any], Path]] | None:
    from agent.project_data import project_tools_for

    rows = project_tools_for(project_id)
    if not rows:
        return None
    loaded: list[tuple[str, dict[str, Any], Path]] = []
    for row in rows:
        mod = _materialize_module(workspace, row.tool_id, row.source_body, row.module_source)
        if not mod.is_file():
            continue
        params = row.parameters or {"type": "object", "properties": {}, "required": []}
        item = {
            "id": row.tool_id,
            "description": row.description or f"Project tool {row.tool_id}",
            "parameters": params,
        }
        loaded.append((row.tool_id, item, mod))
    return loaded


def load_project_tool_entries(
    project_id: int,
    workspace: Path,
    conversation_id: int | None = None,
) -> list[ProjectToolEntry]:
    from agent.project_data import project_tool_cache_token

    cache_key = (project_id, str(workspace.resolve()), conversation_id or 0)
    mtime = max(project_tool_cache_token(project_id) or 0.0, _mtime_key(workspace))
    cached = _CACHE.get(cache_key)
    if cached and cached[0] == mtime:
        return cached[1]

    allowed_ids: set[str] | None = None
    if conversation_id:
        from projects.shared_tools import attached_tool_ids_for_conversation

        allowed_ids = attached_tool_ids_for_conversation(conversation_id)

    entries: list[ProjectToolEntry] = []
    db_items = _entries_from_db(project_id, workspace)
    if db_items is None:
        raw_items: list[tuple[str, dict[str, Any], Path]] = []
        for item in _load_manifest(workspace):
            if not isinstance(item, dict):
                continue
            tid = str(item.get("id") or "").strip()
            if not tid:
                continue
            mod = tool_module_path(workspace, tid)
            raw_items.append((tid, item, mod))
    else:
        raw_items = db_items

    for tid, item, mod in raw_items:
        if allowed_ids is not None and tid not in allowed_ids:
            continue
        if not mod.is_file():
            continue
        desc = str(item.get("description") or f"Project tool {tid}")
        params = item.get("parameters") or {"type": "object", "properties": {}, "required": []}
        definition = {
            "type": "function",
            "function": {
                "name": tid,
                "description": f"[پروژه] {desc}",
                "parameters": params,
            },
        }
        entries.append(ProjectToolEntry(tool_id=tid, definition=definition, module_path=mod))

    if conversation_id and allowed_ids is not None:
        from projects.models import Conversation
        from projects.shared_tools import (
            definition_for_shared_tool,
            effective_version,
            install_shared_tool_on_workspace,
            list_conversation_shared_tools,
        )

        present = {e.tool_id for e in entries}
        conv = Conversation.objects.filter(pk=conversation_id).first()
        if conv:
            for family, link in list_conversation_shared_tools(conv):
                if family.tool_id in present:
                    continue
                version = effective_version(family, link.pinned_version)
                if not version or not (version.source_body or "").strip():
                    continue
                install_shared_tool_on_workspace(version, workspace, project_id=project_id)
                mod = tool_module_path(workspace, family.tool_id)
                if not mod.is_file():
                    continue
                definition = definition_for_shared_tool(version)
                entries.append(
                    ProjectToolEntry(
                        tool_id=family.tool_id,
                        definition=definition,
                        module_path=mod,
                    )
                )

    _CACHE[cache_key] = (mtime, entries)
    return entries


def invalidate_project_cache(project_id: int, workspace: Path) -> None:
    prefix = (project_id, str(workspace.resolve()))
    for key in list(_CACHE):
        if key[0] == prefix[0] and key[1] == prefix[1]:
            _CACHE.pop(key, None)


def _import_tool_module(module_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {module_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def run_project_tool(
    entry: ProjectToolEntry,
    arguments: dict[str, Any],
    options: AgentOptions,
) -> str:
    module_name = f"aca_project_tool_{options.project_id}_{entry.tool_id}"
    try:
        sys.modules.pop(module_name, None)
        mod = _import_tool_module(entry.module_path, module_name)
        run_fn = getattr(mod, "run", None)
        if not callable(run_fn):
            return tool_result(False, "تابع run در ماژول ابزار پیدا نشد")
        out = run_fn(dict(arguments or {}), options)
        if not isinstance(out, str):
            return tool_result(False, "run باید str برگرداند (OK:/ERROR:)")
        return out
    except Exception as exc:
        return tool_result(False, f"خطا در ابزار سفارشی: {exc}")


def dispatch_project_tool(
    project_id: int | None,
    name: str,
    arguments: dict[str, Any],
    options: AgentOptions,
) -> str | None:
    if not project_id:
        return None
    workspace = options.workspace_path()
    for entry in load_project_tool_entries(
        project_id, workspace, conversation_id=options.conversation_id
    ):
        if entry.tool_id == name:
            return run_project_tool(entry, arguments, options)
    return None


def definitions_for_project(
    project_id: int | None,
    workspace: Path,
    conversation_id: int | None = None,
) -> list[dict[str, Any]]:
    if not project_id:
        return []
    return [
        e.definition
        for e in load_project_tool_entries(project_id, workspace, conversation_id)
    ]
