"""پوشهٔ واحد داده‌های خودِ ایجنت داخل پروژه.

فقط همین یک پوشه (`.aca`) برای دادهٔ سنگین ساخته می‌شود.
ایجنت حق خواندن، دیدن ساختار، یا ویرایش داخل آن را ندارد.
"""

from __future__ import annotations

import re
from pathlib import Path

AGENT_STORE_DIR = ".aca"
LEGACY_AGENT_DIRS = (".agent", ".agent-sessions")
PRIVATE_DIR_NAMES = frozenset({AGENT_STORE_DIR, *LEGACY_AGENT_DIRS})

PRIVATE_DENIED_MESSAGE = "این مسیر داخلی ایجنت است و قابل خواندن یا ویرایش نیست"

_PRIVATE_CMD = re.compile(
    r"(?:^|[\s\"'=:/\\])(?:\.agent-sessions|\.aca|\.agent)(?:/|\\|\s|$|[\"'])"
)


def is_private_relative(rel: str | None) -> bool:
    text = (rel or "").strip().replace("\\", "/").lstrip("/")
    if text in ("", "."):
        return False
    parts = [part for part in text.split("/") if part and part != "."]
    return any(part in PRIVATE_DIR_NAMES for part in parts)


def path_is_private(root: Path, rel: str | None) -> bool:
    if is_private_relative(rel):
        return True
    try:
        target = (Path(root) / (rel or ".")).resolve()
        resolved = target.relative_to(Path(root).resolve()).as_posix()
    except (ValueError, OSError):
        return False
    return is_private_relative(resolved)


def command_mentions_private_store(command: str) -> bool:
    return bool(_PRIVATE_CMD.search(command or ""))


def diff_mentions_private_store(diff_text: str) -> bool:
    for line in (diff_text or "").splitlines():
        if line.startswith(("+++", "---", "diff ", "Index:", "*** ", "=== ")):
            if command_mentions_private_store(line):
                return True
    return False


def agent_store(workspace: Path) -> Path:
    return Path(workspace) / AGENT_STORE_DIR


def ensure_agent_store(workspace: Path) -> Path:
    """فقط یک پوشه در ریشهٔ پروژه. زیرپوشه‌ها موقع نیاز ساخته می‌شوند."""
    root = Path(workspace)
    path = agent_store(root)
    path.mkdir(parents=True, exist_ok=True)
    ensure_git_exclude(root)
    return path


def ensure_git_exclude(workspace: Path) -> None:
    git_dir = Path(workspace) / ".git"
    if not git_dir.is_dir():
        return
    info = git_dir / "info"
    try:
        info.mkdir(parents=True, exist_ok=True)
        exclude = info / "exclude"
        existing = exclude.read_text(encoding="utf-8") if exclude.is_file() else ""
        missing = [f"{name}/" for name in sorted(PRIVATE_DIR_NAMES) if f"{name}/" not in existing]
        if not missing:
            return
        prefix = ""
        if existing and not existing.endswith("\n"):
            prefix = "\n"
        with exclude.open("a", encoding="utf-8") as handle:
            handle.write(prefix + "\n".join(missing) + "\n")
    except OSError:
        return


def checkpoints_dir(workspace: Path) -> Path:
    path = agent_store(workspace) / "checkpoints"
    path.mkdir(parents=True, exist_ok=True)
    return path


def backups_dir(workspace: Path, *, create: bool = False) -> Path:
    path = agent_store(workspace) / "backups"
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def telegram_session_dir(workspace: Path) -> Path:
    path = agent_store(workspace) / "sessions" / "telegram"
    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_tools_root(workspace: Path) -> Path:
    return agent_store(workspace) / "runtime" / "custom_tools"
