"""مقایسهٔ وضعیت پروژه قبل/بعد هر نوبت ایجنت (بر اساس بک‌آپ پیام)."""

from __future__ import annotations

import difflib
import json
from pathlib import Path
from typing import Any

from agent.message_backup import (
    BackupError,
    backup_before_state_for_path,
    backup_is_partial_token,
    iter_project_entries,
    manifest_paths_for_token,
    resolve_backup_dir,
    undo_restore_targets,
)
from agent.store import is_private_relative

_MAX_FILE_BYTES = 512 * 1024
_MAX_FILES_PER_TURN = 80
_TEXT_SAMPLE = 8192
_DIFF_CONTEXT_LINES = 3


class MessageBackupMissing(Exception):
    pass


def _is_probably_text(data: bytes) -> bool:
    if not data:
        return True
    if b"\x00" in data[:_TEXT_SAMPLE]:
        return False
    try:
        data[:_TEXT_SAMPLE].decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def _read_file_bytes(path: Path) -> bytes | None:
    try:
        if not path.is_file() or path.is_symlink():
            return None
        size = path.stat().st_size
        if size > _MAX_FILE_BYTES:
            return None
        return path.read_bytes()
    except OSError:
        return None


def _decode_text(data: bytes | None) -> str | None:
    if data is None:
        return None
    if not _is_probably_text(data):
        return None
    return data.decode("utf-8", errors="replace")


def _files_from_project_root(root: Path) -> dict[str, bytes]:
    root = root.resolve()
    out: dict[str, bytes] = {}
    for rel, kind, _target in iter_project_entries(root):
        if kind != "file" or is_private_relative(rel):
            continue
        data = _read_file_bytes(root / rel)
        if data is not None:
            out[rel] = data
    return out


def _files_from_backup_token(token: str, project_root: Path) -> dict[str, bytes]:
    store = resolve_backup_dir(token, project_root)
    manifest_path = store / "manifest.json"
    payload = store / "payload"
    if not manifest_path.is_file():
        raise BackupError("مانیفست بک‌آپ پیدا نشد")
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BackupError(f"مانیفست بک‌آپ خوانده نشد: {exc}") from exc
    entries = raw.get("entries") if isinstance(raw, dict) else None
    if not isinstance(entries, list):
        raise BackupError("مانیفست بک‌آپ نامعتبر است")
    out: dict[str, bytes] = {}
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("kind") != "file":
            continue
        rel = entry.get("path")
        if not isinstance(rel, str) or is_private_relative(rel):
            continue
        data = _read_file_bytes(payload / rel)
        if data is not None:
            out[rel] = data
    return out


def _snapshots_equal(a: bytes | None, b: bytes | None) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return a == b


def _line_stats(before: str | None, after: str | None) -> tuple[int, int]:
    if before is None and after is None:
        return 0, 0
    if before is None:
        return len(after.splitlines()), 0
    if after is None:
        return 0, len(before.splitlines())
    ins = dels = 0
    for tag, _i1, _i2, _j1, _j2 in difflib.SequenceMatcher(
        None, before.splitlines(), after.splitlines()
    ).get_opcodes():
        if tag == "insert":
            ins += _j2 - _j1
        elif tag == "delete":
            dels += _i2 - _i1
        elif tag == "replace":
            dels += _i2 - _i1
            ins += _j2 - _j1
    return ins, dels


def _merged_context_ranges(
    changed: set[int], line_count: int, context: int
) -> list[tuple[int, int]]:
    if not changed or line_count <= 0:
        return []
    ranges: list[tuple[int, int]] = []
    for i in sorted(changed):
        start = max(0, i - context)
        end = min(line_count, i + context + 1)
        if ranges and start <= ranges[-1][1]:
            ranges[-1] = (ranges[-1][0], max(ranges[-1][1], end))
        else:
            ranges.append((start, end))
    return ranges


def _omitted_lines_banner(prev_range_end: int, next_range_start: int) -> str:
    """متن جداکننده بین دو بلوک diff (شماره خطوط ۱-مبنا)."""
    omitted_start = prev_range_end
    omitted_end = next_range_start - 1
    if omitted_end < omitted_start:
        return "— بخش میانی برای خوانایی نمایش داده نشده —"
    count = omitted_end - omitted_start + 1
    line_from = omitted_start + 1
    line_to = omitted_end + 1
    if line_from == line_to:
        return f"▼ {count} خط (شماره {line_from}) برای خوانایی نمایش داده نشده ▼"
    return (
        f"▼ {count} خط (شماره {line_from} تا {line_to}) "
        f"برای خوانایی نمایش داده نشده ▼"
    )


def _slice_lines_for_display(
    lines: list[str],
    marks: list[str],
    context: int = _DIFF_CONTEXT_LINES,
) -> tuple[list[str], list[str], list[int | None]]:
    n = len(lines)
    if n == 0:
        return [], [], []
    changed = {i for i, mark in enumerate(marks) if mark != " "}
    ranges = _merged_context_ranges(changed, n, context)
    if not ranges:
        nums = list(range(1, n + 1))
        return lines, marks, nums
    out_lines: list[str] = []
    out_marks: list[str] = []
    out_nums: list[int | None] = []
    for ri, (start, end) in enumerate(ranges):
        if ri > 0:
            prev_end = ranges[ri - 1][1]
            out_lines.append(_omitted_lines_banner(prev_end, start))
            out_marks.append(" ")
            out_nums.append(None)
        for i in range(start, end):
            out_lines.append(lines[i])
            out_marks.append(marks[i])
            out_nums.append(i + 1)
    return out_lines, out_marks, out_nums


def _highlight_lines(before: str | None, after: str | None) -> dict[str, Any]:
    before_lines = (before or "").splitlines()
    after_lines = (after or "").splitlines()
    before_marks: list[str] = [" " for _ in before_lines]
    after_marks: list[str] = [" " for _ in after_lines]
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
        None, before_lines, after_lines
    ).get_opcodes():
        if tag == "delete":
            for i in range(i1, i2):
                before_marks[i] = "-"
        elif tag == "insert":
            for j in range(j1, j2):
                after_marks[j] = "+"
        elif tag == "replace":
            for i in range(i1, i2):
                before_marks[i] = "-"
            for j in range(j1, j2):
                after_marks[j] = "+"
    b_lines, b_marks, b_nums = _slice_lines_for_display(before_lines, before_marks)
    a_lines, a_marks, a_nums = _slice_lines_for_display(after_lines, after_marks)
    return {
        "before_lines": b_lines,
        "after_lines": a_lines,
        "before_marks": b_marks,
        "after_marks": a_marks,
        "before_line_numbers": b_nums,
        "after_line_numbers": a_nums,
    }


def _public_file_map(files: dict[str, bytes]) -> dict[str, bytes]:
    return {rel: data for rel, data in files.items() if not is_private_relative(rel)}


def file_maps_differ(before_files: dict[str, bytes], after_files: dict[str, bytes]) -> bool:
    before_files = _public_file_map(before_files)
    after_files = _public_file_map(after_files)
    paths = set(before_files) | set(after_files)
    for rel in paths:
        if not _snapshots_equal(before_files.get(rel), after_files.get(rel)):
            return True
    return False


def diff_file_maps(
    before_files: dict[str, bytes],
    after_files: dict[str, bytes],
) -> list[dict[str, Any]]:
    before_files = _public_file_map(before_files)
    after_files = _public_file_map(after_files)
    paths = sorted(set(before_files) | set(after_files))
    changes: list[dict[str, Any]] = []
    for rel in paths:
        if len(changes) >= _MAX_FILES_PER_TURN:
            break
        b = before_files.get(rel)
        a = after_files.get(rel)
        if _snapshots_equal(b, a):
            continue
        if b is None:
            status = "added"
        elif a is None:
            status = "removed"
        else:
            status = "modified"
        before_text = _decode_text(b)
        after_text = _decode_text(a)
        ins, dels = _line_stats(before_text, after_text)
        entry: dict[str, Any] = {
            "path": rel,
            "status": status,
            "insertions": ins,
            "deletions": dels,
            "binary": before_text is None and after_text is None and (b is not None or a is not None),
        }
        if not entry["binary"]:
            entry.update(_highlight_lines(before_text, after_text))
        changes.append(entry)
    return changes


def _reconstruct_file_at_turn_end(
    project_root: Path,
    ordered_assistants: list,
    turn_idx: int,
    path: str,
) -> bytes | None:
    for j in range(turn_idx + 1, len(ordered_assistants)):
        token = ordered_assistants[j].backup.token
        if path not in manifest_paths_for_token(token, project_root):
            continue
        store = resolve_backup_dir(token, project_root)
        payload = store / "payload"
        manifest_path = store / "manifest.json"
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            break
        entries = raw.get("entries") if isinstance(raw, dict) else None
        if not isinstance(entries, list):
            break
        entry = next((e for e in entries if e.get("path") == path), None)
        if not isinstance(entry, dict):
            break
        if entry.get("kind") == "absent":
            return None
        if entry.get("kind") == "file":
            return _read_file_bytes(payload / path)
    return _read_file_bytes(project_root / path)


def _after_files_for_assistant_turn(
    conv,
    assistant_message,
    ordered_assistants: list,
) -> dict[str, bytes]:
    project_root = Path(conv.project.root_path)
    idx = next(
        (i for i, m in enumerate(ordered_assistants) if m.id == assistant_message.id),
        -1,
    )
    if idx < 0:
        return _files_from_project_root(project_root)
    try:
        before_files = _files_from_backup_token(
            assistant_message.backup.token, project_root
        )
    except (MessageBackupMissing, BackupError):
        before_files = {}
    paths = set(before_files.keys())
    try:
        token = assistant_message.backup.token
        paths |= manifest_paths_for_token(token, project_root)
    except BackupError:
        pass
    out: dict[str, bytes] = {}
    for rel in paths:
        data = _reconstruct_file_at_turn_end(project_root, ordered_assistants, idx, rel)
        if data is not None:
            out[rel] = data
    return out


def file_restore_preview_for_message(
    conv, assistant_message, rel_path: str
) -> dict:
    project_root = Path(conv.project.root_path)
    rel_path = rel_path.replace("\\", "/").strip().lstrip("/")
    if not rel_path or is_private_relative(rel_path):
        raise ValueError("مسیر فایل نامعتبر است")
    token = assistant_message.backup.token
    if not backup_is_partial_token(token, project_root):
        return {
            "assistant_message_id": assistant_message.id,
            "path": rel_path,
            "legacy_full_backup": True,
            "modified_after_turn": False,
            "later_turns_touching": 0,
            "needs_confirmation": True,
        }
    assistants = assistant_messages_with_backup(conv)
    turn_idx = next(
        (i for i, m in enumerate(assistants) if m.id == assistant_message.id),
        -1,
    )
    if turn_idx < 0:
        raise ValueError("پیام در این مکالمه پیدا نشد")
    backup_before_state_for_path(token, project_root, rel_path)
    current = _read_file_bytes(project_root / rel_path)
    end_of_turn = _reconstruct_file_at_turn_end(
        project_root, assistants, turn_idx, rel_path
    )
    modified_after = not _snapshots_equal(current, end_of_turn)
    later_turns = sum(
        1
        for j in range(turn_idx + 1, len(assistants))
        if rel_path
        in manifest_paths_for_token(assistants[j].backup.token, project_root)
    )
    return {
        "assistant_message_id": assistant_message.id,
        "path": rel_path,
        "legacy_full_backup": False,
        "modified_after_turn": modified_after,
        "later_turns_touching": later_turns,
        "needs_confirmation": modified_after or later_turns > 0,
    }


def undo_preview_for_message(conv, assistant_message) -> dict:
    project_root = Path(conv.project.root_path)
    assistants = assistant_messages_with_backup(conv)
    undo_index = next(
        (i for i, m in enumerate(assistants) if m.id == assistant_message.id),
        -1,
    )
    if undo_index < 0:
        raise ValueError("پیام در این مکالمه پیدا نشد")
    token = assistant_message.backup.token
    if not backup_is_partial_token(token, project_root):
        return {
            "assistant_message_id": assistant_message.id,
            "files_to_restore": None,
            "conflicts": [],
            "needs_confirmation": True,
            "legacy_full_backup": True,
        }
    targets = undo_restore_targets(assistants, undo_index, project_root)
    conflicts: list[dict] = []
    for path in targets:
        current = _read_file_bytes(project_root / path)
        end_of_turn = _reconstruct_file_at_turn_end(
            project_root, assistants, undo_index, path
        )
        if _snapshots_equal(current, end_of_turn):
            continue
        later_turns = sum(
            1
            for j in range(undo_index + 1, len(assistants))
            if path in manifest_paths_for_token(assistants[j].backup.token, project_root)
        )
        conflicts.append(
            {
                "path": path,
                "modified_after_turn": True,
                "later_turns_touching": later_turns,
            }
        )
    return {
        "assistant_message_id": assistant_message.id,
        "files_to_restore": len(targets),
        "conflicts": conflicts,
        "needs_confirmation": bool(conflicts),
        "legacy_full_backup": False,
    }


def assistant_messages_with_backup(conv) -> list:
    from projects.models import ChatMessage

    msgs = list(
        ChatMessage.objects.filter(
            conversation=conv,
            role=ChatMessage.ROLE_ASSISTANT,
        )
        .select_related("backup")
        .order_by("created_at", "id")
    )
    out = []
    for m in msgs:
        try:
            _ = m.backup
        except Exception:
            continue
        out.append(m)
    return out


def _user_preview_for_assistant(conv, assistant_message) -> str:
    from projects.models import ChatMessage

    user = (
        ChatMessage.objects.filter(
            conversation=conv,
            role=ChatMessage.ROLE_USER,
            created_at__lte=assistant_message.created_at,
        )
        .order_by("-created_at", "-id")
        .first()
    )
    if not user:
        return ""
    text = (user.content or "").strip()
    return text[:120] + ("…" if len(text) > 120 else "")


def turn_code_changes(
    conv,
    assistant_message,
    ordered_assistants: list | None = None,
) -> dict[str, Any]:
    try:
        token = assistant_message.backup.token
    except Exception as exc:
        raise MessageBackupMissing(str(exc)) from exc
    project_root = Path(conv.project.root_path)
    before_files = _files_from_backup_token(token, project_root)
    assistants = (
        ordered_assistants
        if ordered_assistants is not None
        else assistant_messages_with_backup(conv)
    )
    after_files = _after_files_for_assistant_turn(conv, assistant_message, assistants)
    try:
        manifest_paths = manifest_paths_for_token(token, project_root)
    except BackupError:
        manifest_paths = set(before_files)
    scope_paths = manifest_paths | set(before_files) | set(after_files)
    scoped_before = {p: before_files.get(p) for p in scope_paths}
    scoped_after = {p: after_files.get(p) for p in scope_paths}
    files = diff_file_maps(scoped_before, scoped_after)
    ins = sum(f.get("insertions", 0) for f in files)
    dels = sum(f.get("deletions", 0) for f in files)
    return {
        "assistant_message_id": assistant_message.id,
        "user_preview": _user_preview_for_assistant(conv, assistant_message),
        "created_at": assistant_message.created_at.isoformat(),
        "summary": {
            "files_changed": len(files),
            "insertions": ins,
            "deletions": dels,
        },
        "files": files,
        "truncated": len(files) >= _MAX_FILES_PER_TURN,
    }


def assistant_has_code_changes(
    conv,
    assistant_message,
    ordered_assistants: list | None = None,
) -> bool:
    try:
        token = assistant_message.backup.token
    except Exception:
        return False
    try:
        project_root = Path(conv.project.root_path)
        before_files = _files_from_backup_token(token, project_root)
        assistants = (
            ordered_assistants
            if ordered_assistants is not None
            else assistant_messages_with_backup(conv)
        )
        after_files = _after_files_for_assistant_turn(conv, assistant_message, assistants)
        try:
            manifest_paths = manifest_paths_for_token(token, project_root)
        except BackupError:
            manifest_paths = set(before_files)
        scope_paths = manifest_paths | set(before_files) | set(after_files)
        scoped_before = {p: before_files.get(p) for p in scope_paths}
        scoped_after = {p: after_files.get(p) for p in scope_paths}
        return file_maps_differ(scoped_before, scoped_after)
    except BackupError:
        return False


def conversation_code_changes(conv) -> dict[str, Any]:
    assistants = assistant_messages_with_backup(conv)
    turns: list[dict[str, Any]] = []
    total_files = 0
    total_ins = 0
    total_dels = 0
    for m in assistants:
        try:
            block = turn_code_changes(conv, m, assistants)
        except (MessageBackupMissing, BackupError):
            continue
        if not block["summary"]["files_changed"]:
            continue
        block["can_undo"] = True
        turns.append(block)
        total_files += block["summary"]["files_changed"]
        total_ins += block["summary"]["insertions"]
        total_dels += block["summary"]["deletions"]
    return {
        "conversation_id": conv.id,
        "summary": {
            "turns_with_changes": len(turns),
            "files_changed": total_files,
            "insertions": total_ins,
            "deletions": total_dels,
        },
        "turns": turns,
    }
