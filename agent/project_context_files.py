"""فایل‌های همیشه‌در-context و مسیرهای ممنوعِ محتوا (سطح پروژه)."""

from pathlib import Path

from django.conf import settings

from agent.ignore import should_skip_file
from agent.scope import normalize_scope_paths, path_is_denied
from agent.workspace import WorkspaceError, resolve_in_workspace


def always_context_snippet(
    workspace_root: Path,
    paths: list[str] | None,
    *,
    max_chars: int | None = None,
) -> str:
    """محتوای فایل‌های پروژه که در هر نوبت به system message اضافه می‌شود."""
    rels = normalize_scope_paths(paths)
    if not rels:
        return ""
    cap = max_chars or int(getattr(settings, "AGENT_ALWAYS_CONTEXT_CHARS", 16000))
    root = workspace_root.resolve()
    parts: list[str] = []
    used = 0
    for rel in rels:
        try:
            target = resolve_in_workspace(root, rel)
        except WorkspaceError:
            parts.append(f"--- {rel} ---\n(unreadable path)")
            continue
        if not target.is_file():
            parts.append(f"--- {rel} ---\n(not a file)")
            continue
        if should_skip_file(target):
            parts.append(f"--- {rel} ---\n(skipped: binary or ignored)")
            continue
        try:
            text = target.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            parts.append(f"--- {rel} ---\n(read error: {e})")
            continue
        block = f"--- {rel} ---\n{text}"
        if used + len(block) > cap:
            remain = cap - used
            if remain > 80:
                parts.append(block[:remain] + "\n...(truncated)")
            parts.append("...(more always-context files omitted)")
            break
        parts.append(block)
        used += len(block)
    if not parts:
        return ""
    return "Always-available project files (full content each turn):\n" + "\n\n".join(parts)


def enforce_not_denied(rel_path: str, denied_paths: list[str] | None) -> None:
    if path_is_denied(rel_path, denied_paths or []):
        joined = ", ".join(normalize_scope_paths(denied_paths))
        raise WorkspaceError(
            f"File content denied by project policy: '{rel_path}'. "
            f"Blocked paths: {joined}. "
            "You may see the path in the tree but cannot read or edit its content."
        )
