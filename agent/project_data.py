"""دادهٔ سبک ایجنت که در دیتابیس می‌ماند، به‌همراه انتقال فایل‌های قدیمی."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from agent.store import (
    checkpoints_dir,
    ensure_agent_store,
    runtime_tools_root,
    telegram_session_dir,
)


def _db_call(fn, default=None):
    try:
        return fn()
    except Exception as exc:
        name = type(exc).__name__
        if "Database" in name or name in {"OperationalError", "InterfaceError"}:
            return default
        raise


def prepare_project_store(project) -> None:
    if project is None:
        return
    root = Path(project.root_path)
    if not root.is_dir():
        return
    ensure_agent_store(root)
    migrate_legacy_agent_files(project)


def read_project_memory(project_id: int | None) -> str:
    if not project_id:
        return ""

    def _read() -> str:
        from projects.models import Project, ProjectMemory

        project = Project.objects.filter(pk=project_id).first()
        if project is None:
            return ""
        prepare_project_store(project)
        mem = ProjectMemory.objects.filter(project=project).first()
        return (mem.content if mem else "").strip()

    return _db_call(_read, "") or ""


def project_note_text(project_id: int | None, action: str, content: str) -> tuple[bool, str]:
    if not project_id:
        return False, "project_id برای یادداشت پروژه الزامی است"

    def _act() -> tuple[bool, str]:
        from projects.models import Project, ProjectMemory

        project = Project.objects.filter(pk=project_id).first()
        if project is None:
            return False, "پروژه برای ذخیره یادداشت پیدا نشد"
        prepare_project_store(project)
        mem, _created = ProjectMemory.objects.get_or_create(project=project)
        act = (action or "read").strip().lower()
        if act == "read":
            text = (mem.content or "").strip()
            if not text:
                return True, "(یادداشت خالی — با action=append بنویسید)"
            return True, mem.content
        if act not in ("append", "write"):
            return False, "action باید read|append|write باشد"
        body = (content or "").strip()
        if act == "append" and (mem.content or "").strip():
            mem.content = mem.content.rstrip() + "\n\n" + body + "\n"
        else:
            mem.content = (body + "\n") if body else ""
        mem.save(update_fields=["content", "updated_at"])
        return True, "یادداشت پروژه ذخیره شد"

    result = _db_call(_act, None)
    if result is None:
        return False, "ذخیره یادداشت در دیتابیس ممکن نشد"
    return result


def append_debug_attempt(project_id: int | None, entry: dict[str, Any]) -> None:
    if not project_id:
        return

    def _append() -> None:
        from projects.models import ProjectDebugState

        state, _created = ProjectDebugState.objects.get_or_create(project_id=project_id)
        attempts = list(state.attempts or [])
        attempts.append(entry)
        state.attempts = attempts[-200:]
        state.save(update_fields=["attempts", "updated_at"])

    _db_call(_append, None)


def save_debug_recovery(project_id: int | None, text: str) -> None:
    if not project_id:
        return

    def _save() -> None:
        from projects.models import ProjectDebugState

        state, _created = ProjectDebugState.objects.get_or_create(project_id=project_id)
        state.last_recovery = text
        state.save(update_fields=["last_recovery", "updated_at"])

    _db_call(_save, None)


def save_debug_escalation(project_id: int | None, text: str) -> None:
    if not project_id:
        return

    def _save() -> None:
        from projects.models import ProjectDebugState

        state, _created = ProjectDebugState.objects.get_or_create(project_id=project_id)
        marker = "[ارجاع به کاربر]\n"
        state.last_recovery = marker + text
        state.save(update_fields=["last_recovery", "updated_at"])

    _db_call(_save, None)


def upsert_instagram_session(project_id: int | None, username: str, payload: dict) -> bool:
    if not project_id or not username:
        return False

    def _save() -> bool:
        from projects.models import Project, ProjectSession

        if not Project.objects.filter(pk=project_id).exists():
            return False
        ProjectSession.objects.update_or_create(
            project_id=project_id,
            kind=ProjectSession.KIND_INSTAGRAM,
            account_key=username,
            defaults={"payload": payload},
        )
        return True

    return bool(_db_call(_save, False))


def instagram_session_exists(project_id: int | None, username: str) -> bool:
    if not project_id or not username:
        return False

    def _exists() -> bool:
        from projects.models import ProjectSession

        return ProjectSession.objects.filter(
            project_id=project_id,
            kind=ProjectSession.KIND_INSTAGRAM,
            account_key=username,
        ).exists()

    return bool(_db_call(_exists, False))


def upsert_project_tool(
    *,
    project_id: int | None,
    tool_id: str,
    description: str,
    parameters: dict[str, Any],
    source_body: str,
    shared_public_id: str = "",
    module_source: str = "",
) -> None:
    if not project_id:
        return

    def _save() -> None:
        from projects.models import Project, ProjectTool

        if not Project.objects.filter(pk=project_id).exists():
            return
        ProjectTool.objects.update_or_create(
            project_id=project_id,
            tool_id=tool_id,
            defaults={
                "description": (description or "")[:2000],
                "parameters": parameters or {},
                "source_body": source_body or "",
                "shared_public_id": shared_public_id or "",
                "module_source": module_source or "",
            },
        )

    _db_call(_save, None)


def project_tools_for(project_id: int | None) -> list:
    if not project_id:
        return []

    def _load():
        from projects.models import ProjectTool

        return list(ProjectTool.objects.filter(project_id=project_id).order_by("tool_id"))

    return _db_call(_load, []) or []


def project_tool_cache_token(project_id: int | None) -> float | None:
    if not project_id:
        return None

    def _token() -> float | None:
        from django.db.models import Max

        from projects.models import ProjectTool

        agg = ProjectTool.objects.filter(project_id=project_id).aggregate(m=Max("updated_at"))
        moment = agg.get("m")
        if moment is None:
            return None
        return moment.timestamp()

    return _db_call(_token, None)


def migrate_legacy_agent_files(project) -> None:
    root = Path(project.root_path)
    if not root.is_dir():
        return
    legacy = root / ".agent"
    sessions = root / ".agent-sessions"
    if not legacy.exists() and not sessions.exists():
        return
    try:
        _migrate_memory(project, legacy / "PROJECT_MEMORY.md")
        _migrate_debug(project, legacy / "debug")
        _migrate_custom_tools(project, legacy / "custom_tools")
        _relocate_children(legacy / "checkpoints", checkpoints_dir(root))
        _migrate_instagram(project, sessions / "instagram")
        _relocate_children(sessions / "telegram", telegram_session_dir(root))
        _prune_empty(legacy)
        _prune_empty(sessions)
    except OSError:
        return


def _migrate_memory(project, path: Path) -> None:
    if not path.is_file():
        return
    from projects.models import ProjectMemory

    text = path.read_text(encoding="utf-8", errors="replace")
    mem, _created = ProjectMemory.objects.get_or_create(project=project)
    if not (mem.content or "").strip() and text.strip():
        mem.content = text if text.endswith("\n") else text + "\n"
        mem.save(update_fields=["content", "updated_at"])
    path.unlink()


def _migrate_debug(project, debug_dir: Path) -> None:
    if not debug_dir.exists():
        return
    from projects.models import ProjectDebugState

    state, _created = ProjectDebugState.objects.get_or_create(project=project)
    attempts_path = debug_dir / "attempts.jsonl"
    recovery_path = debug_dir / "last_recovery.md"
    if attempts_path.is_file() and not state.attempts:
        rows = []
        for line in attempts_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                rows.append(item)
        state.attempts = rows[-200:]
    if recovery_path.is_file() and not (state.last_recovery or "").strip():
        state.last_recovery = recovery_path.read_text(encoding="utf-8", errors="replace")
    state.save(update_fields=["attempts", "last_recovery", "updated_at"])
    shutil.rmtree(debug_dir, ignore_errors=True)


def _migrate_custom_tools(project, custom_root: Path) -> None:
    manifest_path = custom_root / "manifest.json"
    if not manifest_path.is_file():
        return
    from projects.models import ProjectTool

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    tools = raw.get("tools") if isinstance(raw, dict) else None
    if not isinstance(tools, list):
        return
    dest_tools = runtime_tools_root(Path(project.root_path)) / "tools"
    dest_tools.mkdir(parents=True, exist_ok=True)
    for item in tools:
        if not isinstance(item, dict):
            continue
        tid = str(item.get("id") or "").strip()
        if not tid:
            continue
        src = custom_root / "tools" / f"{tid}.py"
        module_source = ""
        if src.is_file():
            module_source = src.read_text(encoding="utf-8", errors="replace")
            target = dest_tools / f"{tid}.py"
            if not target.is_file():
                target.write_text(module_source, encoding="utf-8")
        if ProjectTool.objects.filter(project=project, tool_id=tid).exists():
            continue
        params = item.get("parameters")
        if not isinstance(params, dict):
            params = {"type": "object", "properties": {}, "required": []}
        ProjectTool.objects.create(
            project=project,
            tool_id=tid,
            description=str(item.get("description") or "")[:2000],
            parameters=params,
            source_body="",
            shared_public_id=str(item.get("shared_public_id") or ""),
            module_source=module_source,
        )
    shutil.rmtree(custom_root, ignore_errors=True)


def _migrate_instagram(project, session_dir: Path) -> None:
    if not session_dir.is_dir():
        return
    from projects.models import ProjectSession

    for path in session_dir.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            payload = {}
        ProjectSession.objects.update_or_create(
            project=project,
            kind=ProjectSession.KIND_INSTAGRAM,
            account_key=path.stem,
            defaults={"payload": payload},
        )
        path.unlink(missing_ok=True)
    _prune_empty(session_dir)


def _relocate_children(src: Path, dest: Path) -> None:
    if not src.is_dir():
        return
    dest.mkdir(parents=True, exist_ok=True)
    for child in list(src.iterdir()):
        target = dest / child.name
        if target.exists():
            continue
        shutil.move(str(child), str(target))
    _prune_empty(src)


def _prune_empty(path: Path) -> None:
    if not path.is_dir():
        return
    for child in sorted(path.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if child.is_dir():
            try:
                child.rmdir()
            except OSError:
                pass
    try:
        path.rmdir()
    except OSError:
        pass
