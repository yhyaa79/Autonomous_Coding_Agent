"""دسترسی یکسان به workspace محلی یا SSH."""

from __future__ import annotations

import fnmatch
import os
import posixpath
import stat as stat_mod
from pathlib import Path
from typing import Iterator

from django.conf import settings

from agent.ignore import should_skip_dir, should_skip_file
from agent.remote_ssh import RemoteSSHError, RemoteSSHSession
from agent.store import PRIVATE_DIR_NAMES, is_private_relative, path_is_private
from agent.workspace import WorkspaceError, resolve_in_workspace

from projects.remote_server import RemoteServerConfig, resolve_remote_relative


class WorkspaceIO:
    is_remote: bool = False

    def root_display(self) -> str:
        raise NotImplementedError

    def resolve_rel(self, relative_path: str) -> str:
        """مسیر نسبی نرمال (برای private/scope)."""
        rel = (relative_path or ".").strip().replace("\\", "/")
        if rel in ("", "/"):
            rel = "."
        if rel.startswith("/"):
            raise WorkspaceError(f"Path outside workspace: {relative_path}")
        parts = posixpath.normpath(rel).split("/")
        if ".." in parts:
            raise WorkspaceError(f"Path outside workspace: {relative_path}")
        return rel if rel != "." else "."

    def path_is_private(self, rel: str) -> bool:
        raise NotImplementedError

    def exists(self, rel: str) -> bool:
        raise NotImplementedError

    def is_file(self, rel: str) -> bool:
        raise NotImplementedError

    def is_dir(self, rel: str) -> bool:
        raise NotImplementedError

    def read_bytes(self, rel: str) -> bytes:
        raise NotImplementedError

    def read_text(self, rel: str) -> str:
        return self.read_bytes(rel).decode("utf-8", errors="replace")

    def write_text(self, rel: str, content: str, *, append: bool = False) -> None:
        data = content.encode("utf-8")
        if append and self.exists(rel) and self.is_file(rel):
            data = self.read_bytes(rel) + data
        self.write_bytes(rel, data)

    def write_bytes(self, rel: str, data: bytes) -> None:
        raise NotImplementedError

    def mkdir_parents(self, rel: str) -> None:
        raise NotImplementedError

    def unlink(self, rel: str) -> None:
        raise NotImplementedError

    def move(self, src_rel: str, dest_rel: str) -> None:
        raise NotImplementedError

    def list_names(self, rel_dir: str) -> list[tuple[str, bool]]:
        """(name, is_dir)"""
        raise NotImplementedError

    def walk_entries(self, base_rel: str) -> Iterator[tuple[str, bool]]:
        """yield (relative_path, is_dir) under base."""
        raise NotImplementedError

    def run_shell(self, command: str, cwd_rel: str, timeout: int) -> tuple[int, str, str]:
        raise NotImplementedError

    def run_patch(self, diff_text: str, timeout: int) -> tuple[int, str, str]:
        raise NotImplementedError

    def close(self) -> None:
        pass


class LocalWorkspaceIO(WorkspaceIO):
    is_remote = False

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def root_display(self) -> str:
        return str(self._root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, rel: str) -> Path:
        rel_n = self.resolve_rel(rel)
        if rel_n == ".":
            return self._root
        return resolve_in_workspace(self._root, rel_n)

    def path_is_private(self, rel: str) -> bool:
        rel_n = self.resolve_rel(rel)
        return path_is_private(self._root, rel_n)

    def exists(self, rel: str) -> bool:
        return self._path(rel).exists()

    def is_file(self, rel: str) -> bool:
        return self._path(rel).is_file()

    def is_dir(self, rel: str) -> bool:
        p = self._path(rel)
        return p.is_dir()

    def read_bytes(self, rel: str) -> bytes:
        p = self._path(rel)
        if not p.is_file():
            raise WorkspaceError(f"Not a file: {rel}")
        if should_skip_file(p):
            raise WorkspaceError(f"File skipped (binary or too large): {rel}")
        max_bytes = int(getattr(settings, "AGENT_MAX_READ_BYTES", 2_000_000))
        raw = p.read_bytes()
        if len(raw) > max_bytes:
            raise WorkspaceError(f"File too large (>{max_bytes} bytes): {rel}")
        return raw

    def write_bytes(self, rel: str, data: bytes) -> None:
        p = self._path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def mkdir_parents(self, rel: str) -> None:
        self._path(rel).parent.mkdir(parents=True, exist_ok=True)

    def unlink(self, rel: str) -> None:
        self._path(rel).unlink()

    def move(self, src_rel: str, dest_rel: str) -> None:
        import shutil

        s = self._path(src_rel)
        d = self._path(dest_rel)
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(s), str(d))

    def list_names(self, rel_dir: str) -> list[tuple[str, bool]]:
        base = self._path(rel_dir)
        if not base.is_dir():
            raise WorkspaceError(f"Not a directory: {rel_dir}")
        out: list[tuple[str, bool]] = []
        for p in sorted(base.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if p.is_dir() and should_skip_dir(p.name):
                continue
            out.append((p.name, p.is_dir()))
        return out

    def walk_entries(self, base_rel: str) -> Iterator[tuple[str, bool]]:
        base = self._path(base_rel)
        if not base.is_dir():
            return
        root = self._root
        for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
            dirnames[:] = [d for d in dirnames if d not in PRIVATE_DIR_NAMES and not should_skip_dir(d)]
            current = Path(dirpath)
            rel_dir = current.relative_to(root).as_posix()
            if rel_dir and rel_dir != ".":
                yield rel_dir, True
            for name in filenames:
                p = current / name
                if should_skip_file(p):
                    continue
                rel = p.relative_to(root).as_posix()
                if is_private_relative(rel):
                    continue
                yield rel, False

    def run_shell(self, command: str, cwd_rel: str, timeout: int) -> tuple[int, str, str]:
        import subprocess

        work = self._path(cwd_rel)
        if not work.is_dir():
            raise WorkspaceError(f"Not a directory: {cwd_rel}")
        proc = subprocess.run(
            command,
            shell=True,
            cwd=work,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out, ""

    def run_patch(self, diff_text: str, timeout: int) -> tuple[int, str, str]:
        import subprocess

        try:
            proc = subprocess.run(
                ["patch", "-p1", "--forward", "--batch"],
                input=diff_text,
                cwd=self._root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError:
            return 127, "", "patch not found"
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out, ""


class RemoteWorkspaceIO(WorkspaceIO):
    is_remote = True

    def __init__(self, session: RemoteSSHSession) -> None:
        self._session = session
        self._root = posixpath.normpath(session.config.remote_root_path)
        self._allow_wide = bool(session.config.allow_server_wide_paths)

    def resolve_rel(self, relative_path: str) -> str:
        if self._allow_wide:
            rel = (relative_path or ".").strip().replace("\\", "/")
            if rel.startswith("/"):
                p = posixpath.normpath(rel)
                if ".." in p.split("/"):
                    raise WorkspaceError(f"Path outside workspace: {relative_path}")
                return p
        return super().resolve_rel(relative_path)

    def root_display(self) -> str:
        return f"ssh://{self._session.config.username}@{self._session.config.host}:{self._session.config.port}{self._root}"

    @property
    def remote_root(self) -> str:
        return self._root

    def _rel_to_abs(self, rel: str) -> str:
        rel_n = self.resolve_rel(rel)
        if rel_n == ".":
            return self._root
        if self._allow_wide and rel_n.startswith("/"):
            return rel_n
        return resolve_remote_relative(
            self._root,
            rel_n,
            allow_server_wide=self._allow_wide,
        )

    def path_is_private(self, rel: str) -> bool:
        rel_n = self.resolve_rel(rel)
        return is_private_relative(rel_n if rel_n != "." else "")

    def _sftp_stat(self, abs_path: str):
        try:
            return self._session.sftp().stat(abs_path)
        except OSError as exc:
            raise WorkspaceError(str(exc)) from exc

    def exists(self, rel: str) -> bool:
        try:
            self._sftp_stat(self._rel_to_abs(rel))
            return True
        except WorkspaceError:
            return False

    def is_file(self, rel: str) -> bool:
        try:
            st = self._sftp_stat(self._rel_to_abs(rel))
        except WorkspaceError:
            return False
        return stat_mod.S_ISREG(st.st_mode)

    def is_dir(self, rel: str) -> bool:
        try:
            st = self._sftp_stat(self._rel_to_abs(rel))
        except WorkspaceError:
            return False
        return stat_mod.S_ISDIR(st.st_mode)

    def read_bytes(self, rel: str) -> bytes:
        abs_p = self._rel_to_abs(rel)
        if not self.is_file(rel):
            raise WorkspaceError(f"Not a file: {rel}")
        max_bytes = int(getattr(settings, "AGENT_MAX_READ_BYTES", 2_000_000))
        sftp = self._session.sftp()
        try:
            st = sftp.stat(abs_p)
        except OSError as exc:
            raise WorkspaceError(str(exc)) from exc
        if st.st_size > max_bytes:
            raise WorkspaceError(f"File too large (>{max_bytes} bytes): {rel}")
        name = posixpath.basename(abs_p)
        if name and should_skip_file(Path(name)):
            raise WorkspaceError(f"File skipped (binary or too large): {rel}")
        with sftp.open(abs_p, "rb") as fh:
            return fh.read()

    def write_bytes(self, rel: str, data: bytes) -> None:
        abs_p = self._rel_to_abs(rel)
        parent = posixpath.dirname(abs_p)
        self._mkdir_p(parent)
        sftp = self._session.sftp()
        with sftp.open(abs_p, "wb") as fh:
            fh.write(data)

    def _mkdir_p(self, abs_dir: str) -> None:
        sftp = self._session.sftp()
        parts = abs_dir.split("/")
        cur = "/" if abs_dir.startswith("/") else ""
        for part in parts:
            if not part:
                continue
            cur = cur + "/" + part if cur else part
            if cur == "":
                cur = "/"
            try:
                sftp.stat(cur)
            except OSError:
                sftp.mkdir(cur)

    def mkdir_parents(self, rel: str) -> None:
        abs_p = self._rel_to_abs(rel)
        parent = posixpath.dirname(abs_p)
        self._mkdir_p(parent)

    def unlink(self, rel: str) -> None:
        self._session.sftp().remove(self._rel_to_abs(rel))

    def move(self, src_rel: str, dest_rel: str) -> None:
        src = self._rel_to_abs(src_rel)
        dest = self._rel_to_abs(dest_rel)
        self._mkdir_p(posixpath.dirname(dest))
        self._session.sftp().rename(src, dest)

    def list_names(self, rel_dir: str) -> list[tuple[str, bool]]:
        abs_dir = self._rel_to_abs(rel_dir)
        if not self.is_dir(rel_dir):
            raise WorkspaceError(f"Not a directory: {rel_dir}")
        sftp = self._session.sftp()
        out: list[tuple[str, bool]] = []
        for attr in sftp.listdir_attr(abs_dir):
            name = attr.filename
            if name in (".", ".."):
                continue
            if stat_mod.S_ISDIR(attr.st_mode) and should_skip_dir(name):
                continue
            out.append((name, stat_mod.S_ISDIR(attr.st_mode)))
        out.sort(key=lambda x: (not x[1], x[0].lower()))
        return out

    def walk_entries(self, base_rel: str) -> Iterator[tuple[str, bool]]:
        base_abs = self._rel_to_abs(base_rel)
        if not self.is_dir(base_rel):
            return
        stack = [base_abs]
        while stack:
            current = stack.pop()
            rel_base = posixpath.relpath(current, self._root)
            if rel_base == ".":
                rel_base = ""
            try:
                items = self._session.sftp().listdir_attr(current)
            except OSError:
                continue
            dirs: list[str] = []
            for attr in items:
                name = attr.filename
                if name in (".", ".."):
                    continue
                child_abs = posixpath.join(current, name)
                rel = posixpath.join(rel_base, name) if rel_base else name
                rel = rel.replace("\\", "/")
                if is_private_relative(rel):
                    continue
                if stat_mod.S_ISDIR(attr.st_mode):
                    if should_skip_dir(name):
                        continue
                    dirs.append(child_abs)
                    yield rel, True
                elif stat_mod.S_ISREG(attr.st_mode):
                    if should_skip_file(Path(name)):
                        continue
                    yield rel, False
            stack.extend(reversed(dirs))

    def run_shell(self, command: str, cwd_rel: str, timeout: int) -> tuple[int, str, str]:
        cwd_abs = self._rel_to_abs(cwd_rel)
        if not self.is_dir(cwd_rel):
            raise WorkspaceError(f"Not a directory: {cwd_rel}")
        try:
            return self._session.exec_command(command, cwd_abs, timeout)
        except RemoteSSHError as exc:
            raise WorkspaceError(str(exc)) from exc

    def run_patch(self, diff_text: str, timeout: int) -> tuple[int, str, str]:
        import base64
        import shlex

        payload = base64.b64encode(diff_text.encode("utf-8")).decode("ascii")
        cmd = f"echo {shlex.quote(payload)} | base64 -d | patch -p1 --forward --batch"
        try:
            code, out, err = self._session.exec_command(cmd, self._root, timeout)
        except RemoteSSHError as exc:
            return 1, "", str(exc)
        return code, (out or "") + (err or ""), ""

    def close(self) -> None:
        self._session.close()


def get_workspace_io(options) -> WorkspaceIO:
    holder = getattr(options, "remote_session", None)
    if holder is not None:
        return RemoteWorkspaceIO(holder)
    return LocalWorkspaceIO(options.workspace_path())


def attach_remote_session(options, config: RemoteServerConfig | None) -> None:
    if config is None:
        options.remote_session = None
        return
    options.remote_session = RemoteSSHSession(config)


def close_remote_session(options) -> None:
    holder = getattr(options, "remote_session", None)
    if holder is not None:
        try:
            holder.close()
        except OSError:
            pass
    options.remote_session = None
