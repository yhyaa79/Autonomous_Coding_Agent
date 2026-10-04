from pathlib import Path

from django.conf import settings

from agent.store import PRIVATE_DIR_NAMES

DEFAULT_DIR_NAMES = {
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".next",
    ".turbo",
    "coverage",
    "htmlcov",
}


def ignore_dir_names() -> set[str]:
    extra = getattr(settings, "AGENT_IGNORE_DIRS", "")
    names = set(DEFAULT_DIR_NAMES)
    names.update(PRIVATE_DIR_NAMES)
    if extra:
        names.update(p.strip() for p in extra.split(",") if p.strip())
    return names


def should_skip_dir(name: str) -> bool:
    return name in ignore_dir_names()


def should_skip_file(path: Path) -> bool:
    if path.name == ".DS_Store":
        return True
    suffix_block = {".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe", ".zip", ".tar", ".gz"}
    if path.suffix.lower() in suffix_block:
        return True
    try:
        if path.stat().st_size > getattr(settings, "AGENT_MAX_READ_BYTES", 2_000_000):
            return True
    except OSError:
        return True
    return False
