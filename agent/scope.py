import re

from .workspace import WorkspaceError

_PATH_LINE = re.compile(
    r"^[\w.\-]+(?:/[\w.\-]+)*(?:\.[\w]+)?$",
    re.UNICODE,
)


def paths_from_scope_note(note: str) -> list[str]:
    """خطوط یادداشت focus که شبیه مسیر فایل/پوشه هستند."""
    out: list[str] = []
    for line in (note or "").splitlines():
        token = line.strip().strip("`-•*،,")
        if not token or " " in token or len(token) > 400:
            continue
        token = token.replace("\\", "/").strip("/")
        if _PATH_LINE.match(token):
            out.append(token)
    return out


def merge_scope_paths(*groups: list[str] | None) -> list[str]:
    return normalize_scope_paths(
        [p for g in groups if g for p in g]
    )


def normalize_scope_paths(paths: list[str] | None) -> list[str]:
    if not paths:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for raw in paths:
        p = (raw or "").strip().replace("\\", "/").strip("/")
        if not p or p == ".":
            continue
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def path_in_scope(rel_path: str, scope_paths: list[str]) -> bool:
    if not scope_paths:
        return True
    rel = (rel_path or "").strip().replace("\\", "/").strip("/")
    if rel in (".", ""):
        return True
    for scope in scope_paths:
        if rel == scope or rel.startswith(scope + "/"):
            return True
    return False


SEARCH_CONTENT_OUTSIDE_FOCUS = (
    "(outside focus — match location only; use read_file inside focus for content)"
)


def format_search_match(
    rel_path: str,
    line_no: int,
    line_text: str,
    content_scope: list[str],
) -> str:
    if not content_scope or path_in_scope(rel_path, content_scope):
        return f"{rel_path}:{line_no}:{line_text[:200]}"
    return f"{rel_path}:{line_no}:{SEARCH_CONTENT_OUTSIDE_FOCUS}"


def path_is_denied(rel_path: str, denied_paths: list[str]) -> bool:
    if not denied_paths:
        return False
    rel = (rel_path or "").strip().replace("\\", "/").strip("/")
    if rel in (".", ""):
        return False
    for denied in normalize_scope_paths(denied_paths):
        if rel == denied or rel.startswith(denied + "/"):
            return True
    return False


def enforce_content_scope(rel_path: str, content_scope: list[str]) -> None:
    """محدودیت خواندن/نوشتن محتوا — نه لیست نام فایل‌ها در پروژه."""
    if not content_scope:
        return
    if not path_in_scope(rel_path, content_scope):
        joined = ", ".join(content_scope)
        raise WorkspaceError(
            f"File content outside focus: '{rel_path}'. "
            f"read_file/write/patch allowed only under: {joined}. "
            "You may still use project_tree, list_directory, glob_files for paths anywhere. "
            "Ask the user to add paths to focus if you need to edit/read that file."
        )


def enforce_scope(rel_path: str, scope_paths: list[str]) -> None:
    """Alias — محدودیت محتوا (سازگاری با کد قبلی)."""
    enforce_content_scope(rel_path, scope_paths)
