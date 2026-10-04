"""بک‌آپ فایل‌های در حال تغییر توسط ایجنت و بازگردانی (جزئی یا کامل برای نسخه‌های قدیمی)."""

from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path

import fcntl
from django.conf import settings

from agent.store import (
    PRIVATE_DIR_NAMES,
    agent_store,
    backups_dir,
    ensure_agent_store,
)

# محیط، وابستگی و کش. سورس، تنظیمات و .git داخل بک‌آپ هستند
# تا Undo واقعاً پروژه را به همان درخت فایل برگرداند.
SKIP_DIR_NAMES = frozenset(
    {
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        "htmlcov",
        ".next",
        ".turbo",
        "coverage",
    }
)

_TOKEN_RE = re.compile(r"^[a-f0-9]{32}$")
_MANIFEST_VERSION = 1
_MANIFEST_VERSION_PARTIAL = 2


class BackupError(Exception):
    pass


def legacy_backup_root() -> Path:
    """انبار قدیمی بیرون از پروژه؛ فقط برای خواندن بک‌آپ‌های قبلی."""
    path = Path(settings.AGENT_MESSAGE_BACKUP_DIR).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _checked_token_dir(parent: Path, token: str) -> Path:
    if not _TOKEN_RE.fullmatch(token or ""):
        raise BackupError("شناسه بک‌آپ نامعتبر است")
    parent = parent.resolve()
    path = (parent / token).resolve()
    if path.parent != parent:
        raise BackupError("شناسه بک‌آپ نامعتبر است")
    return path


def new_backup_dir(project_root: Path, token: str) -> Path:
    parent = backups_dir(Path(project_root), create=True)
    return _checked_token_dir(parent, token)


def resolve_backup_dir(token: str, project_root: Path) -> Path:
    """بک‌آپ جدید داخل پروژه؛ اگر نباشد نسخهٔ قدیمی سراسری."""
    primary = _checked_token_dir(backups_dir(Path(project_root), create=False), token)
    if (primary / "manifest.json").is_file():
        return primary
    legacy = _checked_token_dir(legacy_backup_root(), token)
    if (legacy / "manifest.json").is_file():
        return legacy
    return primary


def remove_backup_tree(token: str, project_root: Path | None = None) -> None:
    if not _TOKEN_RE.fullmatch(token or ""):
        return
    candidates: list[Path] = []
    if project_root is not None:
        try:
            candidates.append(
                _checked_token_dir(backups_dir(Path(project_root), create=False), token)
            )
        except BackupError:
            pass
    try:
        candidates.append(_checked_token_dir(legacy_backup_root(), token))
    except BackupError:
        pass
    for path in candidates:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)


@contextmanager
def project_backup_lock(project_id: int):
    """قفل روی کل پروژه تا بک‌آپ، اجرای ایجنت و Undo همزمان درخت را خراب نکنند."""
    from projects.models import Project
    from projects.remote_server import project_uses_remote

    project = Project.objects.filter(pk=int(project_id)).only("id", "root_path").first()
    if project is not None and project_uses_remote(project):
        lock_dir = legacy_backup_root() / "locks"
    elif project is not None and Path(project.root_path).is_dir():
        lock_dir = ensure_agent_store(Path(project.root_path)) / "locks"
    else:
        lock_dir = legacy_backup_root() / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / f"project-{int(project_id)}.lock"
    handle = open(lock_path, "a+")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except (ValueError, OSError):
        return False


def _skip_dir(path: Path, store: Path) -> bool:
    if path.name in SKIP_DIR_NAMES or path.name in PRIVATE_DIR_NAMES:
        return True
    if path.is_symlink():
        return False
    try:
        resolved = path.resolve()
    except OSError:
        return True
    return resolved == store or _is_under(resolved, store)


def _safe_relative(rel: str) -> Path:
    if not isinstance(rel, str) or not rel or rel.startswith(("/", "\\")):
        raise BackupError("مسیر نامعتبر در بک‌آپ")
    path = Path(rel)
    if path.is_absolute() or ".." in path.parts:
        raise BackupError(f"مسیر نامعتبر در بک‌آپ: {rel}")
    return path


def _inside(root: Path, rel: str) -> Path:
    rel_path = _safe_relative(rel)
    candidate = root / rel_path
    root_resolved = root.resolve()
    parent_resolved = candidate.parent.resolve()
    if parent_resolved != root_resolved and not _is_under(parent_resolved, root_resolved):
        raise BackupError(f"مسیر خارج از پروژه: {rel}")
    return candidate


def iter_project_entries(root: Path):
    """فایل، سیم‌لینک و پوشهٔ قابل بازگردانی. وارد venv و خودِ انبار بک‌آپ نمی‌شود."""
    root = root.resolve()
    if not root.is_dir():
        raise BackupError("پوشه پروژه وجود ندارد")
    store = agent_store(root).resolve()
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current = Path(dirpath)
        rel_dir = current.relative_to(root).as_posix()
        if rel_dir != ".":
            yield rel_dir, "dir", None

        kept_dirs: list[str] = []
        symlink_dirs: list[str] = []
        for name in dirnames:
            child = current / name
            if _skip_dir(child, store):
                continue
            if child.is_symlink():
                symlink_dirs.append(name)
                continue
            kept_dirs.append(name)
        dirnames[:] = kept_dirs

        for name in symlink_dirs:
            child = current / name
            rel = child.relative_to(root).as_posix()
            try:
                target = os.readlink(child)
            except OSError as exc:
                raise BackupError(f"خواندن لینک {rel} ناموفق بود: {exc}") from exc
            yield rel, "symlink", target

        for name in filenames:
            if name.startswith(".aca-copy-"):
                continue
            child = current / name
            rel = child.relative_to(root).as_posix()
            try:
                if child.is_symlink():
                    yield rel, "symlink", os.readlink(child)
                elif child.is_file():
                    yield rel, "file", None
            except OSError as exc:
                raise BackupError(f"خواندن {rel} ناموفق بود: {exc}") from exc


def snapshot_project(root: Path, dest: Path) -> int:
    root = Path(root).resolve()
    if dest.exists():
        shutil.rmtree(dest)
    payload = dest / "payload"
    payload.mkdir(parents=True)
    entries: list[dict] = []
    try:
        for rel, kind, target in iter_project_entries(root):
            if kind == "file":
                src = root / rel
                out = payload / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, out)
                entries.append({"path": rel, "kind": "file"})
            elif kind == "symlink":
                entries.append({"path": rel, "kind": "symlink", "target": target})
            else:
                entries.append({"path": rel, "kind": "dir"})
        manifest = {"version": _MANIFEST_VERSION, "entries": entries}
        tmp = dest / "manifest.json.tmp"
        tmp.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, dest / "manifest.json")
    except Exception:
        shutil.rmtree(dest, ignore_errors=True)
        raise
    return sum(1 for entry in entries if entry["kind"] != "dir")


def _read_manifest(manifest_path: Path) -> dict:
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BackupError(f"مانیفست بک‌آپ خوانده نشد: {exc}") from exc
    if not isinstance(raw, dict):
        raise BackupError("مانیفست بک‌آپ نامعتبر است")
    version = raw.get("version")
    if version not in (_MANIFEST_VERSION, _MANIFEST_VERSION_PARTIAL):
        raise BackupError("نسخه بک‌آپ پشتیبانی نمی‌شود")
    return raw


def manifest_is_partial(raw: dict) -> bool:
    if raw.get("partial") is True:
        return True
    return raw.get("version") == _MANIFEST_VERSION_PARTIAL


def _load_entries(manifest_path: Path, payload: Path) -> list[dict]:
    raw = _read_manifest(manifest_path)
    entries = raw.get("entries")
    if not isinstance(entries, list):
        raise BackupError("مانیفست بک‌آپ نامعتبر است")
    seen: set[str] = set()
    clean: list[dict] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise BackupError("رکورد نامعتبر در بک‌آپ")
        rel = entry.get("path")
        kind = entry.get("kind")
        if not isinstance(rel, str) or kind not in (
            "file",
            "dir",
            "symlink",
            "absent",
        ):
            raise BackupError("رکورد نامعتبر در بک‌آپ")
        _safe_relative(rel)
        if rel in seen:
            raise BackupError(f"مسیر تکراری در بک‌آپ: {rel}")
        seen.add(rel)
        if kind == "absent":
            clean.append({"path": rel, "kind": "absent"})
            continue
        if kind == "file":
            src = _inside(payload, rel)
            if not src.is_file():
                raise BackupError(f"فایل بک‌آپ پیدا نشد: {rel}")
            clean.append({"path": rel, "kind": "file"})
        elif kind == "symlink":
            target = entry.get("target")
            if not isinstance(target, str) or "\x00" in target:
                raise BackupError(f"مقصد لینک نامعتبر است: {rel}")
            clean.append({"path": rel, "kind": "symlink", "target": target})
        else:
            clean.append({"path": rel, "kind": "dir"})
    return clean


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _atomic_copy(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.parent / f".aca-copy-{uuid.uuid4().hex}"
    try:
        shutil.copy2(src, tmp)
        os.replace(tmp, dest)
    except Exception:
        if tmp.exists() or tmp.is_symlink():
            tmp.unlink()
        raise


def _restore_entry(root: Path, payload: Path, entry: dict) -> None:
    dest = _inside(root, entry["path"])
    kind = entry["kind"]
    if kind == "dir":
        if dest.is_symlink():
            dest.unlink()
        elif dest.exists() and not dest.is_dir():
            dest.unlink()
        dest.mkdir(parents=True, exist_ok=True)
        return
    if kind == "symlink":
        if dest.is_symlink() or dest.exists():
            _remove_path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(entry["target"], dest)
        return
    if dest.is_symlink():
        dest.unlink()
    elif dest.is_dir():
        shutil.rmtree(dest)
    _atomic_copy(_inside(payload, entry["path"]), dest)


def _purge_bytecode(root: Path, keep: set[str]) -> None:
    """کش بایت‌کدِ بعد از بک‌آپ را پاک می‌کند تا سورسِ برگشته با .pyc کهنه اجرا نشود."""
    store = agent_store(root).resolve()
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current = Path(dirpath)
        kept: list[str] = []
        for name in dirnames:
            child = current / name
            if child.is_symlink():
                continue
            rel = child.relative_to(root).as_posix()
            if name == "__pycache__" and rel not in keep:
                shutil.rmtree(child, ignore_errors=True)
                continue
            if _skip_dir(child, store):
                continue
            kept.append(name)
        dirnames[:] = kept
        for name in filenames:
            target = current / name
            rel = target.relative_to(root).as_posix()
            if name.startswith(".aca-copy-") or (
                name.endswith((".pyc", ".pyo")) and rel not in keep
            ):
                try:
                    target.unlink()
                except OSError:
                    pass


def _remove_extra_empty_dirs(root: Path, snapshot_dirs: set[str]) -> None:
    store = agent_store(root).resolve()
    found: list[Path] = []
    for dirpath, dirnames, _filenames in os.walk(root, topdown=True, followlinks=False):
        current = Path(dirpath)
        kept: list[str] = []
        for name in dirnames:
            child = current / name
            if child.is_symlink() or _skip_dir(child, store):
                continue
            kept.append(name)
        dirnames[:] = kept
        if current != root:
            found.append(current)
    for current in sorted(found, key=lambda p: len(p.parts), reverse=True):
        rel = current.relative_to(root).as_posix()
        if rel in snapshot_dirs:
            continue
        try:
            current.rmdir()
        except OSError:
            pass


def restore_remote_project(project, token: str) -> None:
    from projects.remote_server import project_remote_config

    remote_cfg = project_remote_config(project)
    if not remote_cfg:
        raise BackupError("پروژه راه‌دور تنظیم نشده است")
    from agent.options import AgentOptions
    from agent.remote_backup import new_remote_backup_dir, restore_remote_workspace
    from agent.workspace_io import RemoteWorkspaceIO, attach_remote_session, close_remote_session

    dest = new_remote_backup_dir(project.id, token)
    manifest_path = dest / "manifest.json"
    if not manifest_path.is_file():
        raise BackupError("بک‌آپ ناقص است")
    opts = AgentOptions(workspace_root=remote_cfg.remote_root_path)
    attach_remote_session(opts, remote_cfg)
    try:
        io = RemoteWorkspaceIO(opts.remote_session)
        restore_remote_workspace(io, dest)
    finally:
        close_remote_session(opts)


def restore_project(root: Path, token: str) -> None:
    """پروژه را دقیقاً به درخت بک‌آپ برمی‌گرداند: بازنویسی، حذف اضافه‌ها، احیای حذف‌شده‌ها."""
    root = Path(root).resolve()
    if not root.is_dir():
        raise BackupError("پوشه پروژه وجود ندارد")
    src = resolve_backup_dir(token, root)
    manifest_path = src / "manifest.json"
    payload = src / "payload"
    if not manifest_path.is_file() or not payload.is_dir():
        raise BackupError("بک‌آپ ناقص است")
    if manifest_is_partial(_read_manifest(manifest_path)):
        raise BackupError("این بک‌آپ جزئی است؛ از بازگردانی جزئی استفاده کنید")
    entries = _load_entries(manifest_path, payload)
    snapshot_map = {entry["path"]: entry for entry in entries}

    ordered = sorted(
        entries,
        key=lambda entry: (entry["path"].count("/"), 0 if entry["kind"] == "dir" else 1),
    )
    for entry in ordered:
        _restore_entry(root, payload, entry)

    current = list(iter_project_entries(root))
    extras = [(rel, kind) for rel, kind, _target in current if rel not in snapshot_map]
    for rel, kind in sorted(
        extras,
        key=lambda item: (item[0].count("/"), 0 if item[1] != "dir" else 1),
        reverse=True,
    ):
        target = _inside(root, rel)
        if kind == "dir":
            try:
                target.rmdir()
            except OSError:
                pass
        elif target.exists() or target.is_symlink():
            _remove_path(target)

    snapshot_dirs = {entry["path"] for entry in entries if entry["kind"] == "dir"}
    _remove_extra_empty_dirs(root, snapshot_dirs)
    _purge_bytecode(root, set(snapshot_map))

    leftovers = [
        rel
        for rel, _kind, _target in iter_project_entries(root)
        if rel not in snapshot_map
    ]
    if leftovers:
        sample = "، ".join(leftovers[:8])
        raise BackupError(f"بازگردانی ناقص ماند؛ این مسیرها هنوز فرق دارند: {sample}")
    _verify_restored(root, payload, entries)


def _same_file(src: Path, dest: Path) -> bool:
    if src.stat().st_size != dest.stat().st_size:
        return False
    if (src.stat().st_mode & 0o777) != (dest.stat().st_mode & 0o777):
        return False
    with src.open("rb") as left, dest.open("rb") as right:
        while True:
            chunk_left = left.read(1024 * 1024)
            chunk_right = right.read(1024 * 1024)
            if chunk_left != chunk_right:
                return False
            if not chunk_left:
                return True


def _verify_restored(root: Path, payload: Path, entries: list[dict]) -> None:
    for entry in entries:
        dest = _inside(root, entry["path"])
        kind = entry["kind"]
        if kind == "dir":
            if dest.is_symlink() or not dest.is_dir():
                raise BackupError(f"پوشه بازگردانده نشد: {entry['path']}")
            continue
        if kind == "symlink":
            if not dest.is_symlink() or os.readlink(dest) != entry["target"]:
                raise BackupError(f"لینک بازگردانده نشد: {entry['path']}")
            continue
        src = _inside(payload, entry["path"])
        if dest.is_symlink() or not dest.is_file() or not _same_file(src, dest):
            raise BackupError(f"فایل با بک‌آپ یکی نیست: {entry['path']}")


def _write_manifest(dest: Path, entries: list[dict], *, partial: bool) -> None:
    manifest = {
        "version": _MANIFEST_VERSION_PARTIAL if partial else _MANIFEST_VERSION,
        "partial": partial,
        "entries": entries,
    }
    tmp = dest / "manifest.json.tmp"
    tmp.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, dest / "manifest.json")


def _apply_partial_entry(root: Path, payload: Path, entry: dict) -> None:
    rel = entry["path"]
    kind = entry["kind"]
    dest = _inside(root, rel)
    if kind == "absent":
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        elif dest.is_dir():
            shutil.rmtree(dest)
        return
    if kind == "file":
        if dest.is_symlink():
            dest.unlink()
        elif dest.is_dir():
            shutil.rmtree(dest)
        _atomic_copy(_inside(payload, rel), dest)
        return
    if kind == "symlink":
        if dest.is_symlink() or dest.exists():
            _remove_path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(entry["target"], dest)


def restore_partial_project(root: Path, token: str, entries: list[dict]) -> None:
    """فقط مسیرهای موجود در مانیفست را بازمی‌گرداند (بدون دست‌زدن به بقیهٔ پروژه)."""
    root = Path(root).resolve()
    src = resolve_backup_dir(token, root)
    payload = src / "payload"
    for entry in entries:
        _apply_partial_entry(root, payload, entry)


def apply_partial_file_states(
    root: Path,
    states: dict[str, bytes | None],
    payload_by_path: dict[str, Path] | None = None,
) -> None:
    """states: مسیر -> محتوا؛ None یعنی فایل نباید وجود داشته باشد."""
    for rel, data in states.items():
        dest = _inside(root, rel)
        if data is None:
            if dest.is_symlink() or dest.is_file():
                dest.unlink()
            elif dest.is_dir():
                shutil.rmtree(dest)
            continue
        if dest.is_symlink():
            dest.unlink()
        elif dest.is_dir():
            shutil.rmtree(dest)
        if payload_by_path and rel in payload_by_path:
            _atomic_copy(payload_by_path[rel], dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.parent / f".aca-copy-{uuid.uuid4().hex}"
            try:
                tmp.write_bytes(data)
                os.replace(tmp, dest)
            except Exception:
                if tmp.exists():
                    tmp.unlink()
                raise


def manifest_paths_for_token(token: str, project_root: Path) -> set[str]:
    src = resolve_backup_dir(token, project_root)
    entries = _load_entries(src / "manifest.json", src / "payload")
    return {e["path"] for e in entries}


def backup_is_partial_token(token: str, project_root: Path) -> bool:
    src = resolve_backup_dir(token, project_root)
    return manifest_is_partial(_read_manifest(src / "manifest.json"))


class TurnBackupSession:
    """بک‌آپ تنها فایل‌هایی که در این نوبت ایجنت تغییر می‌کنند."""

    def __init__(self, conv) -> None:
        from projects.remote_server import project_remote_config

        self.conv = conv
        self.project = conv.project
        self.token: str | None = None
        self.dest: Path | None = None
        self.entries: list[dict] = []
        self._paths: set[str] = set()
        self._remote_cfg = project_remote_config(self.project)
        self._io = None

    @property
    def has_files(self) -> bool:
        return bool(self._paths)

    def _ensure_dest(self) -> Path:
        if self.dest is not None:
            return self.dest
        self.token = uuid.uuid4().hex
        if self._remote_cfg:
            from agent.remote_backup import new_remote_backup_dir

            self.dest = new_remote_backup_dir(self.project.id, self.token)
        else:
            project_root = Path(self.project.root_path)
            ensure_agent_store(project_root)
            self.dest = new_backup_dir(project_root, self.token)
        (self.dest / "payload").mkdir(parents=True, exist_ok=True)
        return self.dest

    def _workspace_io(self, options):
        if self._io is not None:
            return self._io
        from agent.workspace_io import get_workspace_io

        self._io = get_workspace_io(options)
        return self._io

    def ensure_file_before_write(self, options, rel_path: str) -> None:
        from agent.store import is_private_relative

        io = self._workspace_io(options)
        rel = io.resolve_rel(rel_path)
        if rel in (".", "") or is_private_relative(rel):
            return
        if rel in self._paths:
            return
        dest = self._ensure_dest()
        payload = dest / "payload"
        entry: dict
        if io.is_file(rel):
            data = io.read_bytes(rel)
            out = payload / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            entry = {"path": rel, "kind": "file"}
        else:
            entry = {"path": rel, "kind": "absent"}
        self.entries.append(entry)
        self._paths.add(rel)

    def rollback_workspace(self, options) -> None:
        if not self._paths or self.dest is None:
            return
        io = self._workspace_io(options)
        payload = self.dest / "payload"
        for entry in self.entries:
            rel = entry["path"]
            kind = entry["kind"]
            if kind == "absent":
                if io.exists(rel):
                    io.unlink(rel)
                continue
            if kind == "file":
                src = payload / rel
                if io.exists(rel):
                    io.unlink(rel)
                io.mkdir_parents(rel)
                io.write_bytes(rel, src.read_bytes())

    def discard(self) -> None:
        if self.dest and self.dest.is_dir():
            shutil.rmtree(self.dest, ignore_errors=True)
        self.dest = None
        self.token = None
        self.entries = []
        self._paths = set()

    def finalize_record(self):
        from projects.models import MessageBackup

        if not self._paths or not self.token or self.dest is None:
            self.discard()
            return None
        _write_manifest(self.dest, self.entries, partial=True)
        return MessageBackup.objects.create(
            project=self.project,
            conversation=self.conv,
            token=self.token,
        )


def ensure_turn_file_backup(options, rel_path: str) -> None:
    session = getattr(options, "turn_backup", None)
    if session is None:
        return
    session.ensure_file_before_write(options, rel_path)


def undo_restore_targets(
    assistants: list,
    undo_index: int,
    project_root: Path,
) -> dict[str, bytes | None]:
    """وضعیت فایل‌ها قبل از نوبت undo_index (همان نوبت و همهٔ نوبت‌های بعد حذف می‌شوند)."""
    targets: dict[str, bytes | None] = {}
    paths: set[str] = set()
    for j in range(undo_index, len(assistants)):
        paths |= manifest_paths_for_token(assistants[j].backup.token, project_root)

    for path in paths:
        first_j = next(
            j
            for j in range(undo_index, len(assistants))
            if path in manifest_paths_for_token(assistants[j].backup.token, project_root)
        )
        token = assistants[first_j].backup.token
        src = resolve_backup_dir(token, project_root)
        entries = _load_entries(src / "manifest.json", src / "payload")
        entry = next(e for e in entries if e["path"] == path)
        if entry["kind"] == "absent":
            targets[path] = None
        elif entry["kind"] == "file":
            targets[path] = (src / "payload" / path).read_bytes()
        else:
            raise BackupError(f"بازگردانی برای نوع {entry['kind']} پشتیبانی نمی‌شود")
    return targets


def backup_before_state_for_path(
    token: str, project_root: Path, path: str
) -> bytes | None:
    """محتوای فایل قبل از نوبت (یا None اگر فایل وجود نداشت)."""
    src = resolve_backup_dir(token, project_root)
    entries = _load_entries(src / "manifest.json", src / "payload")
    entry = next((e for e in entries if e["path"] == path), None)
    if entry is None:
        raise BackupError(f"مسیر در بک‌آپ این نوبت نیست: {path}")
    kind = entry["kind"]
    if kind == "absent":
        return None
    if kind == "file":
        return (src / "payload" / path).read_bytes()
    raise BackupError(f"بازگردانی برای نوع {kind} پشتیبانی نمی‌شود")


def apply_file_states_on_project(
    project,
    states: dict[str, bytes | None],
) -> None:
    from projects.remote_server import project_remote_config

    project_root = Path(project.root_path)
    remote_cfg = project_remote_config(project)
    if remote_cfg:
        from agent.options import AgentOptions
        from agent.workspace_io import RemoteWorkspaceIO, attach_remote_session, close_remote_session

        opts = AgentOptions(workspace_root=remote_cfg.remote_root_path)
        attach_remote_session(opts, remote_cfg)
        try:
            io = RemoteWorkspaceIO(opts.remote_session)
            for rel, data in states.items():
                if data is None:
                    if io.exists(rel):
                        io.unlink(rel)
                else:
                    if io.exists(rel):
                        io.unlink(rel)
                    io.mkdir_parents(rel)
                    io.write_bytes(rel, data)
        finally:
            close_remote_session(opts)
    else:
        apply_partial_file_states(project_root, states)


def apply_undo_partial(
    project,
    assistants: list,
    undo_index: int,
) -> None:
    project_root = Path(project.root_path)
    targets = undo_restore_targets(assistants, undo_index, project_root)
    apply_file_states_on_project(project, targets)


def create_message_backup(conv):
    from projects.models import MessageBackup
    from projects.remote_server import project_remote_config

    token = uuid.uuid4().hex
    remote_cfg = project_remote_config(conv.project)
    if remote_cfg:
        from agent.options import AgentOptions
        from agent.remote_backup import new_remote_backup_dir, snapshot_remote_workspace
        from agent.workspace_io import RemoteWorkspaceIO, attach_remote_session, close_remote_session

        dest = new_remote_backup_dir(conv.project_id, token)
        opts = AgentOptions(workspace_root=remote_cfg.remote_root_path)
        attach_remote_session(opts, remote_cfg)
        try:
            io = RemoteWorkspaceIO(opts.remote_session)
            snapshot_remote_workspace(io, dest)
        except Exception:
            shutil.rmtree(dest, ignore_errors=True)
            raise
        finally:
            close_remote_session(opts)
    else:
        project_root = Path(conv.project.root_path)
        ensure_agent_store(project_root)
        dest = new_backup_dir(project_root, token)
        try:
            snapshot_project(project_root, dest)
        except Exception:
            shutil.rmtree(dest, ignore_errors=True)
            raise
    try:
        return MessageBackup.objects.create(
            project=conv.project,
            conversation=conv,
            token=token,
        )
    except Exception:
        shutil.rmtree(dest, ignore_errors=True)
        raise


def discard_message_backup(backup) -> None:
    backup.delete()


def rollback_message_backup(backup) -> None:
    """اگر اجرای ایجنت خطا داد، پروژه را به بک‌آپ همان نوبت برگردان."""
    from projects.remote_server import project_remote_config

    remote_cfg = project_remote_config(backup.project)
    if remote_cfg:
        from agent.options import AgentOptions
        from agent.remote_backup import new_remote_backup_dir, restore_remote_workspace
        from agent.workspace_io import RemoteWorkspaceIO, attach_remote_session, close_remote_session

        dest = new_remote_backup_dir(backup.project_id, backup.token)
        opts = AgentOptions(workspace_root=remote_cfg.remote_root_path)
        attach_remote_session(opts, remote_cfg)
        try:
            io = RemoteWorkspaceIO(opts.remote_session)
            restore_remote_workspace(io, dest)
        finally:
            close_remote_session(opts)
    else:
        restore_project(Path(backup.project.root_path), backup.token)
    discard_message_backup(backup)
