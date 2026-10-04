from pathlib import Path

from agent.store import PRIVATE_DENIED_MESSAGE, path_is_private


class WorkspaceError(Exception):
    pass


def resolve_in_workspace(workspace: Path, relative_path: str) -> Path:
    """مسیر را نسبت به workspace حل می‌کند و از path traversal جلوگیری می‌کند."""
    workspace = workspace.resolve()
    rel = (relative_path or ".").strip().lstrip("/")
    if path_is_private(workspace, rel):
        raise WorkspaceError(PRIVATE_DENIED_MESSAGE)
    target = (workspace / rel).resolve()
    try:
        target.relative_to(workspace)
    except ValueError:
        raise WorkspaceError(f"Path outside workspace: {relative_path}")
    if path_is_private(workspace, target.relative_to(workspace).as_posix()):
        raise WorkspaceError(PRIVATE_DENIED_MESSAGE)
    return target
