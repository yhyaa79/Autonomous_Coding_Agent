"""بک‌آپ پروژهٔ SSH — snapshot روی دیسک ACA (نه روی سرور راه‌دور)."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from agent.message_backup import (
    BackupError,
    _MANIFEST_VERSION,
    _safe_relative,
    legacy_backup_root,
    new_backup_dir,
)
from agent.workspace_io import RemoteWorkspaceIO


def remote_backup_parent(project_id: int) -> Path:
    path = legacy_backup_root() / "remote-projects" / str(int(project_id))
    path.mkdir(parents=True, exist_ok=True)
    return path


def new_remote_backup_dir(project_id: int, token: str) -> Path:
    parent = remote_backup_parent(project_id)
    from agent.message_backup import _checked_token_dir

    return _checked_token_dir(parent, token)


def snapshot_remote_workspace(io: RemoteWorkspaceIO, dest: Path) -> int:
    if dest.exists():
        import shutil

        shutil.rmtree(dest)
    payload = dest / "payload"
    payload.mkdir(parents=True)
    entries: list[dict] = []
    try:
        for rel, is_dir in io.walk_entries("."):
            if is_dir:
                entries.append({"path": rel, "kind": "dir"})
                continue
            if rel.startswith(".aca/") or rel == ".aca":
                continue
            data = io.read_bytes(rel)
            out = payload / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            entries.append({"path": rel, "kind": "file"})
        manifest = {"version": _MANIFEST_VERSION, "entries": entries}
        tmp = dest / "manifest.json.tmp"
        tmp.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, dest / "manifest.json")
    except Exception:
        import shutil

        shutil.rmtree(dest, ignore_errors=True)
        raise
    return sum(1 for entry in entries if entry["kind"] != "dir")


def entries_paths_seen(entries: list[dict]) -> set[str]:
    return {e["path"] for e in entries if e.get("kind") == "dir"}


def restore_remote_workspace(io: RemoteWorkspaceIO, backup_dir: Path) -> None:
    from agent.message_backup import _inside, _load_entries
    from agent.store import is_private_relative

    manifest = backup_dir / "manifest.json"
    payload = backup_dir / "payload"
    entries = _load_entries(manifest, payload)
    keep_files = {e["path"] for e in entries if e["kind"] == "file"}
    for entry in entries:
        rel = entry["path"]
        kind = entry["kind"]
        if kind == "dir":
            io.mkdir_parents(f"{rel}/.keep")
            continue
        if kind != "file":
            continue
        src = _inside(payload, rel)
        if io.exists(rel):
            if io.is_dir(rel):
                raise BackupError(f"مسیر فایل پوشه است: {rel}")
            io.unlink(rel)
        io.mkdir_parents(rel)
        io.write_bytes(rel, src.read_bytes())
    for rel, is_dir in list(io.walk_entries(".")):
        if is_dir:
            continue
        if rel in keep_files:
            continue
        if rel.startswith(".aca/"):
            continue
        if is_private_relative(rel):
            continue
        try:
            io.unlink(rel)
        except Exception:
            pass
