"""پیاده‌سازی ابزارهای git، وب، checkpoint و غیره."""

import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings

from .ignore import should_skip_dir, should_skip_file
from .options import AgentOptions
from .security import shell_command_allowed
from .store import (
    PRIVATE_DENIED_MESSAGE,
    checkpoints_dir,
    diff_mentions_private_store,
    is_private_relative,
    path_is_private,
)
from .tool_impl import _blocked_private, _io, _root, _scoped_rel, tool_result
from .workspace import WorkspaceError, resolve_in_workspace


def _run_git(args: list[str], options: AgentOptions, cwd: str = ".") -> str:
    io = _io(options)
    cwd_rel = io.resolve_rel(cwd or ".")
    if io.is_remote:
        if not io.is_dir(cwd_rel):
            return tool_result(False, f"Not a directory: {cwd}")
        git_dir = ".." if cwd_rel == "." else f"{cwd_rel}/.git"
        if not io.exists(git_dir) and cwd_rel != ".":
            if not io.exists(".git"):
                return tool_result(False, "این پوشه repo گیت نیست")
        import shlex

        cmd = "git " + " ".join(shlex.quote(a) for a in args)
        try:
            code, out, _err = io.run_shell(cmd, cwd_rel, min(settings.AGENT_COMMAND_TIMEOUT, 90))
        except WorkspaceError as exc:
            return tool_result(False, str(exc))
        return tool_result(code == 0, (out or "").strip() or f"exit {code}")
    work_dir = resolve_in_workspace(_root(options), cwd or ".")
    if not (work_dir / ".git").exists() and work_dir != _root(options):
        if not (_root(options) / ".git").exists():
            return tool_result(False, "این پوشه repo گیت نیست")
    cmd = ["git", *args]
    try:
        proc = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=min(settings.AGENT_COMMAND_TIMEOUT, 90),
        )
    except subprocess.TimeoutExpired:
        return tool_result(False, "git timeout")
    out = (proc.stdout or "") + (proc.stderr or "")
    return tool_result(proc.returncode == 0, out.strip() or f"exit {proc.returncode}")


def git_status(options: AgentOptions, cwd: str = ".") -> str:
    return _run_git(["status", "--short", "--branch"], options, cwd)


def git_diff(options: AgentOptions, cwd: str = ".", staged: bool = False) -> str:
    args = ["diff"]
    if staged:
        args.append("--staged")
    return _run_git(args, options, cwd)


def git_log(options: AgentOptions, cwd: str = ".", max_count: int = 15) -> str:
    n = max(1, min(int(max_count), 50))
    return _run_git(
        ["log", f"-{n}", "--oneline", "--decorate"],
        options,
        cwd,
    )


def git_commit(message: str, options: AgentOptions, cwd: str = ".") -> str:
    if not options.allow_write:
        return tool_result(False, "Write disabled (allow_write=false)")
    msg = (message or "").strip()
    if not msg:
        return tool_result(False, "message الزامی است")
    add = _run_git(
        [
            "add",
            "-A",
            "--",
            ".",
            ":(exclude).aca",
            ":(exclude).agent",
            ":(exclude).agent-sessions",
        ],
        options,
        cwd,
    )
    if add.startswith("ERROR:"):
        return add
    return _run_git(["commit", "-m", msg], options, cwd)


def delete_file(path: str, options: AgentOptions) -> str:
    if not options.allow_write:
        return tool_result(False, "Write disabled (allow_write=false)")
    try:
        _scoped_rel(options, path)
        blocked = _blocked_private(options, path)
        if blocked:
            return blocked
        io = _io(options)
        rel = io.resolve_rel(path)
        if is_private_relative(rel if rel != "." else ""):
            return tool_result(False, PRIVATE_DENIED_MESSAGE)
        if not io.exists(rel):
            return tool_result(False, f"Not found: {path}")
        if io.is_dir(rel):
            return tool_result(False, "مسیر یک پوشه است — از run_shell با احتیاط استفاده کنید")
        io.unlink(rel)
        return tool_result(True, f"Deleted {path}")
    except WorkspaceError as e:
        return tool_result(False, str(e))


def move_file(src: str, dest: str, options: AgentOptions) -> str:
    if not options.allow_write:
        return tool_result(False, "Write disabled (allow_write=false)")
    try:
        _scoped_rel(options, src)
        _scoped_rel(options, dest)
        blocked = _blocked_private(options, src, dest)
        if blocked:
            return blocked
        io = _io(options)
        s_rel = io.resolve_rel(src)
        d_rel = io.resolve_rel(dest)
        for rel in (s_rel, d_rel):
            if rel != "." and is_private_relative(rel):
                return tool_result(False, PRIVATE_DENIED_MESSAGE)
        if not io.exists(s_rel):
            return tool_result(False, f"Source not found: {src}")
        io.mkdir_parents(d_rel)
        io.move(s_rel, d_rel)
        return tool_result(True, f"Moved {src} → {dest}")
    except WorkspaceError as e:
        return tool_result(False, str(e))


def apply_unified_diff(diff_text: str, options: AgentOptions) -> str:
    if not options.allow_write:
        return tool_result(False, "Write disabled (allow_write=false)")
    diff = (diff_text or "").strip()
    if not diff:
        return tool_result(False, "diff خالی است")
    if diff_mentions_private_store(diff):
        return tool_result(False, PRIVATE_DENIED_MESSAGE)
    io = _io(options)
    try:
        code, out, _err = io.run_patch(diff, settings.AGENT_COMMAND_TIMEOUT)
    except WorkspaceError as exc:
        return tool_result(False, str(exc))
    if code == 127 and "not found" in (out or "").lower():
        return tool_result(
            False,
            "دستور patch نصب نیست — از apply_patch استفاده کنید",
        )
    return tool_result(code == 0, (out or "").strip() or f"exit {code}")


def _detect_test_command(root: Path, options: AgentOptions | None = None) -> str | None:
    if options is not None:
        io = _io(options)
        if io.is_remote:
            if io.exists("pytest.ini") or io.exists("pyproject.toml"):
                return "python -m pytest -q --tb=short"
            if io.exists("manage.py"):
                return "python manage.py test --keepdb -v 1"
            if io.exists("package.json"):
                return "npm test --if-present"
            return None
    if (root / "pytest.ini").exists() or (root / "pyproject.toml").exists():
        return "python -m pytest -q --tb=short"
    if (root / "manage.py").exists():
        return "python manage.py test --keepdb -v 1"
    if (root / "package.json").exists():
        return "npm test --if-present"
    return None


def run_tests(command: str | None, options: AgentOptions, cwd: str = ".") -> str:
    if not options.allow_shell:
        return tool_result(False, "Shell disabled (allow_shell=false)")
    cmd = (command or "").strip() or _detect_test_command(_root(options), options)
    if not cmd:
        return tool_result(False, "دستور تست مشخص نیست — command را بدهید")
    blocked = shell_command_allowed(cmd)
    if blocked:
        return tool_result(False, blocked)
    from .tool_impl import run_shell

    return run_shell(cmd, cwd, options)


def format_lint(tool: str, path: str, options: AgentOptions) -> str:
    if not options.allow_shell:
        return tool_result(False, "Shell disabled (allow_shell=false)")
    t = (tool or "ruff").strip().lower()
    rel = (path or ".").strip()
    if t == "ruff":
        cmd = f"python -m ruff check {rel}"
    elif t == "ruff_format":
        cmd = f"python -m ruff format {rel}"
    elif t == "eslint":
        cmd = f"npx eslint {rel}"
    else:
        return tool_result(False, f"ابزار ناشناخته: {tool}")
    blocked = shell_command_allowed(cmd)
    if blocked:
        return tool_result(False, blocked)
    from .tool_impl import run_shell

    return run_shell(cmd, ".", options)


def web_fetch(url: str, options: AgentOptions) -> str:
    u = (url or "").strip()
    if not u.startswith(("http://", "https://")):
        return tool_result(False, "فقط http/https مجاز است")
    max_bytes = int(getattr(settings, "AGENT_WEB_FETCH_MAX_BYTES", 500_000))
    timeout = int(getattr(settings, "AGENT_WEB_FETCH_TIMEOUT", 25))
    req = Request(
        u,
        headers={
            "User-Agent": "ACA-Agent/1.0 (+local coding agent)",
            "Accept": "text/html,application/json,text/plain,*/*",
        },
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read(max_bytes + 1)
    except URLError as e:
        return tool_result(
            False,
            f"خطا در دریافت URL (فیلترینگ/شبکه/SSL): {e}",
        )
    if len(raw) > max_bytes:
        raw = raw[:max_bytes]
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"<script[\s\S]*?</script>", "", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.I)
    if len(text) > 12000:
        text = text[:12000] + "\n...(truncated)"
    return tool_result(True, f"URL: {u}\n\n{text}")


def project_note(action: str, content: str, options: AgentOptions) -> str:
    act = (action or "read").strip().lower()
    if act in ("append", "write") and not options.allow_write:
        return tool_result(False, "Write disabled (allow_write=false)")
    from agent.project_data import project_note_text

    ok, message = project_note_text(options.project_id, act, content)
    return tool_result(ok, message)


def checkpoint_create(paths: list[str], label: str, options: AgentOptions) -> str:
    if not options.allow_write:
        return tool_result(False, "Write disabled (allow_write=false)")
    root = _root(options)
    ck_id = (label or "").strip() or uuid.uuid4().hex[:10]
    ck_id = re.sub(r"[^\w\-]", "_", ck_id)[:40]
    if path_is_private(root, ck_id):
        return tool_result(False, PRIVATE_DENIED_MESSAGE)
    dest_root = checkpoints_dir(root) / ck_id
    if dest_root.exists():
        return tool_result(False, f"checkpoint {ck_id} از قبل وجود دارد")
    copied: list[str] = []
    rel_paths = paths or ["."]
    try:
        dest_root.mkdir(parents=True, exist_ok=False)
        for rel in rel_paths:
            rel = (rel or ".").strip()
            if path_is_private(root, rel):
                return tool_result(False, PRIVATE_DENIED_MESSAGE)
            _scoped_rel(options, rel if rel not in (".", "") else "")
            src = resolve_in_workspace(root, rel)
            if src.is_file():
                if should_skip_file(src):
                    continue
                rel_p = src.relative_to(root).as_posix()
                if is_private_relative(rel_p):
                    continue
                out = dest_root / rel_p
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, out)
                copied.append(rel_p)
            elif src.is_dir():
                for dirpath, dirnames, filenames in os.walk(src):
                    dirnames[:] = [name for name in dirnames if not should_skip_dir(name)]
                    for name in filenames:
                        p = Path(dirpath) / name
                        if should_skip_file(p):
                            continue
                        rel_p = p.relative_to(root).as_posix()
                        if is_private_relative(rel_p):
                            continue
                        out = dest_root / rel_p
                        out.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(p, out)
                        copied.append(rel_p)
        meta = {"id": ck_id, "files": copied[:200]}
        (dest_root / "_meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return tool_result(True, f"checkpoint {ck_id} با {len(copied)} فایل")
    except WorkspaceError as e:
        return tool_result(False, str(e))
    except OSError as e:
        return tool_result(False, str(e))


def checkpoint_restore(checkpoint_id: str, options: AgentOptions) -> str:
    if not options.allow_write:
        return tool_result(False, "Write disabled (allow_write=false)")
    ck = (checkpoint_id or "").strip()
    if not ck:
        return tool_result(False, "checkpoint_id الزامی است")
    root = _root(options)
    if "/" in ck or "\\" in ck or ".." in ck:
        return tool_result(False, "checkpoint_id نامعتبر است")
    src_root = checkpoints_dir(root) / ck
    if not src_root.is_dir():
        return tool_result(False, f"checkpoint پیدا نشد: {ck}")
    restored = 0
    for p in src_root.rglob("*"):
        if p.is_dir() or p.name == "_meta.json":
            continue
        rel = p.relative_to(src_root).as_posix()
        if is_private_relative(rel):
            continue
        try:
            _scoped_rel(options, rel)
            dest = resolve_in_workspace(root, rel)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
            restored += 1
        except WorkspaceError:
            continue
    return tool_result(True, f"بازگردانی {restored} فایل از checkpoint {ck}")
