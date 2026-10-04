import fnmatch
import os
import re
import subprocess
from pathlib import Path

from django.conf import settings

from .ignore import should_skip_dir, should_skip_file
from .options import AgentOptions
from .project_context_files import enforce_not_denied
from .scope import enforce_content_scope, format_search_match
from .store import PRIVATE_DENIED_MESSAGE, PRIVATE_DIR_NAMES, is_private_relative, path_is_private
from .workspace import WorkspaceError, resolve_in_workspace
from .workspace_io import get_workspace_io


def _root(options: AgentOptions) -> Path:
    return options.workspace_path()


def _io(options: AgentOptions):
    return get_workspace_io(options)


def _content_scoped_rel(options: AgentOptions, rel_path: str) -> str:
    rel = (rel_path or ".").strip().replace("\\", "/")
    if rel not in (".", ""):
        enforce_not_denied(rel, options.denied_content_paths)
        enforce_content_scope(rel, options.content_scope())
    return rel


# سازگاری با extra_impl و ابزارهای دیگر
_scoped_rel = _content_scoped_rel


def _blocked_private(options: AgentOptions, *rels: str) -> str | None:
    io = _io(options)
    for rel in rels:
        try:
            rel_n = io.resolve_rel(rel or ".")
        except WorkspaceError:
            return tool_result(False, PRIVATE_DENIED_MESSAGE)
        if rel_n != "." and io.path_is_private(rel_n):
            return tool_result(False, PRIVATE_DENIED_MESSAGE)
    return None


def _iter_visible_files(base: Path, root: Path):
    if base.is_file():
        if not path_is_private(root, base.relative_to(root).as_posix()):
            yield base
        return
    for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
        dirnames[:] = [name for name in dirnames if name not in PRIVATE_DIR_NAMES and not should_skip_dir(name)]
        current = Path(dirpath)
        for name in filenames:
            path = current / name
            rel = path.relative_to(root).as_posix()
            if is_private_relative(rel):
                continue
            yield path


def tool_result(ok: bool, data: str) -> str:
    max_len = getattr(settings, "AGENT_MAX_TOOL_RESULT_CHARS", 12000)
    if len(data) > max_len:
        data = data[:max_len] + "\n...(truncated)"
    prefix = "OK" if ok else "ERROR"
    return f"{prefix}: {data}"


def list_directory(
    path: str,
    recursive: bool,
    max_entries: int,
    options: AgentOptions,
) -> str:
    blocked = _blocked_private(options, path or ".")
    if blocked and (path or ".") not in ("", "."):
        return blocked
    io = _io(options)
    try:
        rel_dir = io.resolve_rel(path or ".")
        if not io.exists(rel_dir):
            return tool_result(False, f"Not found: {path}")
        if not io.is_dir(rel_dir):
            return tool_result(False, f"Not a directory: {path}")

        entries: list[str] = []
        cap = min(max_entries, getattr(settings, "AGENT_LIST_DIR_MAX_ENTRIES", 500))

        if not recursive:
            for name, is_dir in io.list_names(rel_dir):
                if len(entries) >= cap:
                    break
                child_rel = name if rel_dir == "." else f"{rel_dir}/{name}"
                kind = "dir" if is_dir else "file"
                entries.append(f"{kind}\t{child_rel}")
        else:
            for child_rel, is_dir in io.walk_entries(rel_dir):
                if len(entries) >= cap:
                    break
                if is_dir:
                    continue
                entries.append(f"file\t{child_rel}")

        body = "\n".join(entries) if entries else "(empty)"
        if len(entries) >= cap:
            body += "\n...(truncated)"
        return tool_result(True, body)
    except WorkspaceError as e:
        return tool_result(False, str(e))


def project_tree(max_depth: int, max_entries: int, options: AgentOptions) -> str:
    io = _io(options)
    lines: list[str] = []
    cap = min(max_entries, 200)

    def walk(rel_dir: str, depth: int) -> None:
        if len(lines) >= cap or depth > max_depth:
            return
        try:
            children = io.list_names(rel_dir)
        except WorkspaceError:
            return
        for name, is_dir in children:
            if len(lines) >= cap:
                lines.append("...(truncated)")
                return
            child_rel = name if rel_dir == "." else f"{rel_dir}/{name}"
            if is_dir and should_skip_dir(name):
                continue
            if not is_dir and should_skip_file(Path(name)):
                continue
            marker = "/" if is_dir else ""
            lines.append(f"{child_rel}{marker}")
            if is_dir:
                walk(child_rel, depth + 1)

    walk(".", 0)

    return tool_result(True, "\n".join(lines) if lines else "(empty)")


def glob_files(pattern: str, path: str, options: AgentOptions) -> str:
    blocked = _blocked_private(options, path or ".")
    if blocked and (path or ".") not in ("", "."):
        return blocked
    io = _io(options)
    try:
        base_rel = io.resolve_rel(path or ".")
        if not io.is_dir(base_rel):
            return tool_result(False, f"Not a directory: {path}")
        matches: list[str] = []
        cap = getattr(settings, "AGENT_GLOB_MAX_MATCHES", 100)
        for rel, is_dir in io.walk_entries(base_rel):
            if is_dir:
                continue
            if len(matches) >= cap:
                break
            name = Path(rel).name
            if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(name, pattern):
                matches.append(rel)
        matches.sort()
        body = "\n".join(matches) if matches else "(no matches)"
        if len(matches) >= cap:
            body += "\n...(truncated)"
        return tool_result(True, body)
    except WorkspaceError as e:
        return tool_result(False, str(e))


def read_file(
    path: str,
    start_line: int,
    end_line: int | None,
    max_lines: int,
    options: AgentOptions,
) -> str:
    blocked = _blocked_private(options, path)
    if blocked:
        return blocked
    try:
        _content_scoped_rel(options, path)
        io = _io(options)
        if not io.is_file(path):
            return tool_result(False, f"Not a file: {path}")
        text = io.read_text(path)
        lines = text.splitlines()
        start = max(1, start_line)
        end = end_line if end_line is not None else start + max_lines - 1
        end = min(end, len(lines))
        if start > len(lines):
            return tool_result(False, f"start_line {start} beyond file length {len(lines)}")
        slice_lines = lines[start - 1 : end]
        numbered = [f"{i + start:6d}|{line}" for i, line in enumerate(slice_lines)]
        header = f"File: {path} (lines {start}-{end} of {len(lines)})\n"
        return tool_result(True, header + "\n".join(numbered))
    except WorkspaceError as e:
        return tool_result(False, str(e))
    except OSError as e:
        return tool_result(False, str(e))


def write_workspace_text(
    path: str,
    content: str,
    options: AgentOptions,
    *,
    append: bool = False,
) -> str:
    """نوشتن فایل در workspace برای ابزارهای سفارشی — موفق: OK:…؛ خطا: ERROR:…"""
    if not options.allow_write:
        return tool_result(False, "Write disabled (allow_write=false).")
    blocked = _blocked_private(options, path)
    if blocked:
        return blocked
    try:
        _content_scoped_rel(options, path)
        from agent.message_backup import ensure_turn_file_backup, project_backup_lock

        with project_backup_lock(options.project_id):
            ensure_turn_file_backup(options, path)
            io = _io(options)
            io.write_text(path, content, append=append)
        return tool_result(True, f"Wrote {len(content)} bytes to {path}")
    except WorkspaceError as e:
        return tool_result(False, str(e))
    except OSError as e:
        return tool_result(False, str(e))


def read_workspace_text(path: str, options: AgentOptions) -> str:
    """متن کامل فایل برای ابزارهای سفارشی — موفق: متن خام؛ خطا: ERROR:...

    فقط path و options لازم است (برخلاف read_file با start_line/end_line/max_lines).
    """
    blocked = _blocked_private(options, path)
    if blocked:
        return blocked
    try:
        _content_scoped_rel(options, path)
        return _io(options).read_text(path)
    except WorkspaceError as e:
        return tool_result(False, str(e))
    except OSError as e:
        return tool_result(False, str(e))


def write_file(path: str, content: str, options: AgentOptions) -> str:
    if not options.allow_write:
        return tool_result(False, "Write disabled by user (allow_write=false).")
    blocked = _blocked_private(options, path)
    if blocked:
        return blocked
    try:
        _content_scoped_rel(options, path)
        from agent.message_backup import ensure_turn_file_backup, project_backup_lock

        with project_backup_lock(options.project_id):
            ensure_turn_file_backup(options, path)
            io = _io(options)
            io.mkdir_parents(path)
            io.write_text(path, content)
        return tool_result(True, f"Wrote {len(content)} bytes to {path}")
    except WorkspaceError as e:
        return tool_result(False, str(e))
    except OSError as e:
        return tool_result(False, str(e))


def apply_patch(
    path: str, old_string: str, new_string: str, options: AgentOptions
) -> str:
    if not options.allow_write:
        return tool_result(False, "Write disabled by user (allow_write=false).")
    blocked = _blocked_private(options, path)
    if blocked:
        return blocked
    try:
        _content_scoped_rel(options, path)
        io = _io(options)
        if not io.is_file(path):
            return tool_result(False, f"Not a file: {path}")
        content = io.read_text(path)
        count = content.count(old_string)
        if count == 0:
            return tool_result(False, "old_string not found in file")
        if count > 1:
            return tool_result(
                False,
                f"old_string appears {count} times; include more context to make it unique",
            )
        from agent.message_backup import ensure_turn_file_backup, project_backup_lock

        with project_backup_lock(options.project_id):
            ensure_turn_file_backup(options, path)
            io.write_text(path, content.replace(old_string, new_string, 1))
        return tool_result(True, f"Patched {path}")
    except WorkspaceError as e:
        return tool_result(False, str(e))
    except OSError as e:
        return tool_result(False, str(e))


def search_code(
    query: str,
    path: str,
    glob_pattern: str,
    case_sensitive: bool,
    options: AgentOptions,
) -> str:
    blocked = _blocked_private(options, path or ".")
    if blocked and (path or ".") not in ("", "."):
        return blocked
    try:
        search_path = path or "."
        return _search_code_in_path(
            query, search_path, glob_pattern, case_sensitive, options
        )
    except WorkspaceError as e:
        return tool_result(False, str(e))


def _search_code_in_path(
    query: str,
    path: str,
    glob_pattern: str,
    case_sensitive: bool,
    options: AgentOptions,
) -> str:
    io = _io(options)
    if io.is_remote:
        rel = io.resolve_rel(path)
        if getattr(settings, "AGENT_GREP_USE_RG", True):
            rg_result = _search_with_rg_remote(
                query, rel, glob_pattern, case_sensitive, options, io
            )
            if rg_result is not None:
                return rg_result
        return _search_python_remote(query, rel, glob_pattern, case_sensitive, options, io)
    base = resolve_in_workspace(_root(options), path)
    if getattr(settings, "AGENT_GREP_USE_RG", True):
        rg_result = _search_with_rg(query, base, glob_pattern, case_sensitive, options)
        if rg_result is not None:
            return rg_result
    return _search_python(query, base, glob_pattern, case_sensitive, options)


def _search_with_rg(
    query: str,
    base: Path,
    glob_pattern: str,
    case_sensitive: bool,
    options: AgentOptions,
) -> str | None:
    cmd = ["rg", "--no-heading", "--line-number", "--max-count", "5"]
    for name in sorted(PRIVATE_DIR_NAMES):
        cmd.extend(["--glob", f"!{name}/**"])
    if not case_sensitive:
        cmd.append("-i")
    if glob_pattern and glob_pattern != "*":
        cmd.extend(["--glob", glob_pattern])
    cmd.extend([query, str(base)])
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=_root(options),
        )
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return "ERROR: search timed out"

    out = (proc.stdout or "").strip()
    if not out and proc.returncode == 1:
        return "(no matches)"
    if not out:
        return (proc.stderr or "rg failed").strip()

    return _filter_search_lines(out, options)


def _search_python(
    query: str,
    base: Path,
    glob_pattern: str,
    case_sensitive: bool,
    options: AgentOptions,
) -> str:
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        pattern = re.compile(query, flags)
    except re.error:
        pattern = re.compile(re.escape(query), flags)

    matches: list[str] = []
    cap = getattr(settings, "AGENT_SEARCH_MAX_MATCHES", 80)
    root = _root(options)
    content_scope = options.content_scope()
    roots = [base] if base.is_dir() else [base.parent]

    for search_root in roots:
        for p in _iter_visible_files(search_root, root):
            if len(matches) >= cap:
                break
            if should_skip_file(p):
                continue
            rel = p.relative_to(root).as_posix()
            if glob_pattern != "*" and not fnmatch.fnmatch(rel, glob_pattern):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), start=1):
                if pattern.search(line):
                    matches.append(format_search_match(rel, i, line, content_scope))
                    if len(matches) >= cap:
                        break

    body = "\n".join(matches) if matches else "(no matches)"
    if len(matches) >= cap:
        body += "\n...(truncated)"
    return body


def _filter_search_lines(out: str, options: AgentOptions) -> str:
    root = _root(options)
    content_scope = options.content_scope()
    cap = getattr(settings, "AGENT_SEARCH_MAX_MATCHES", 80)
    rel_lines = []
    for line in out.splitlines():
        if len(rel_lines) >= cap:
            break
        try:
            abs_part, rest = line.split(":", 1)
            p = Path(abs_part)
            rel = p.relative_to(root).as_posix()
            if is_private_relative(rel):
                continue
            if ":" in rest:
                line_no_str, line_text = rest.split(":", 1)
                try:
                    line_no = int(line_no_str)
                except ValueError:
                    rel_lines.append(f"{rel}:{rest}")
                    continue
                rel_lines.append(
                    format_search_match(rel, line_no, line_text, content_scope)
                )
            else:
                rel_lines.append(f"{rel}:{rest}")
        except ValueError:
            rel_lines.append(line)
        except Exception:
            rel_lines.append(line)
    body = "\n".join(rel_lines)
    if len(out.splitlines()) > cap:
        body += "\n...(truncated)"
    return body


def _search_with_rg_remote(
    query: str,
    rel_path: str,
    glob_pattern: str,
    case_sensitive: bool,
    options: AgentOptions,
    io,
) -> str | None:
    import shlex

    target = "." if rel_path == "." else rel_path
    parts = ["rg", "--no-heading", "--line-number", "--max-count", "5"]
    for name in sorted(PRIVATE_DIR_NAMES):
        parts.extend(["--glob", shlex.quote(f"!{name}/**")])
    if not case_sensitive:
        parts.append("-i")
    if glob_pattern and glob_pattern != "*":
        parts.extend(["--glob", shlex.quote(glob_pattern)])
    parts.append(shlex.quote(query))
    parts.append(shlex.quote(target))
    shell_cmd = " ".join(parts)
    try:
        code, out, _err = io.run_shell(shell_cmd, rel_path if rel_path != "." else ".", 30)
    except WorkspaceError as exc:
        return f"ERROR: {exc}"
    if code == 127 or "not found" in (out or "").lower():
        return None
    out = (out or "").strip()
    if not out and code == 1:
        return "(no matches)"
    if not out:
        return "rg failed"
    return _filter_search_lines_remote(out, options)


def _search_python_remote(
    query: str,
    rel_path: str,
    glob_pattern: str,
    case_sensitive: bool,
    options: AgentOptions,
    io,
) -> str:
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        pattern = re.compile(query, flags)
    except re.error:
        pattern = re.compile(re.escape(query), flags)

    matches: list[str] = []
    cap = getattr(settings, "AGENT_SEARCH_MAX_MATCHES", 80)
    content_scope = options.content_scope()
    for rel, is_dir in io.walk_entries(rel_path):
        if is_dir:
            continue
        if len(matches) >= cap:
            break
        if glob_pattern != "*" and not fnmatch.fnmatch(rel, glob_pattern):
            continue
        try:
            text = io.read_text(rel)
        except WorkspaceError:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                matches.append(format_search_match(rel, i, line, content_scope))
                if len(matches) >= cap:
                    break

    body = "\n".join(matches) if matches else "(no matches)"
    if len(matches) >= cap:
        body += "\n...(truncated)"
    return body


def _filter_search_lines_remote(out: str, options: AgentOptions) -> str:
    content_scope = options.content_scope()
    cap = getattr(settings, "AGENT_SEARCH_MAX_MATCHES", 80)
    rel_lines = []
    for line in out.splitlines():
        if len(rel_lines) >= cap:
            break
        if ":" not in line:
            rel_lines.append(line)
            continue
        rel, rest = line.split(":", 1)
        if ":" in rest:
            line_no_str, line_text = rest.split(":", 1)
            try:
                line_no = int(line_no_str)
            except ValueError:
                rel_lines.append(f"{rel}:{rest}")
                continue
            rel_lines.append(format_search_match(rel, line_no, line_text, content_scope))
        else:
            rel_lines.append(f"{rel}:{rest}")
    body = "\n".join(rel_lines)
    if len(out.splitlines()) > cap:
        body += "\n...(truncated)"
    return body


def post_instagram_text_story(
    username: str,
    password: str,
    story_text: str,
    options: AgentOptions,
) -> str:
    """انتشار استوری متنی روی اینستاگرام — از run_shell (و SSH پروژه) استفاده می‌کند."""
    import base64
    import shlex
    import textwrap

    user = (username or "").strip()
    pwd = (password or "").strip()
    text = (story_text or "").strip()
    if not user or not pwd:
        return tool_result(False, "username و password الزامی است")
    if not text:
        return tool_result(False, "story_text خالی است")
    if not options.allow_shell:
        return tool_result(False, "Shell غیرفعال است (allow_shell=false)")

    py = textwrap.dedent(
        """
import os
import sys
import tempfile

user = os.environ["ACA_IG_USER"]
password = os.environ["ACA_IG_PASS"]
caption = os.environ["ACA_IG_TEXT"]
try:
    from instagrapi import Client
except ImportError:
    print("instagrapi not installed — run: pip install instagrapi", file=sys.stderr)
    sys.exit(2)
try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Pillow not installed — run: pip install Pillow", file=sys.stderr)
    sys.exit(2)

cl = Client()
cl.login(user, password)
w, h = 1080, 1920
img = Image.new("RGB", (w, h), (24, 24, 24))
draw = ImageDraw.Draw(img)
wrapped = []
line = ""
for word in caption.split():
    trial = (line + " " + word).strip()
    if len(trial) > 28:
        if line:
            wrapped.append(line)
        line = word
    else:
        line = trial
if line:
    wrapped.append(line)
body = "\\n".join(wrapped) if wrapped else caption
draw.multiline_text((80, h // 3), body, fill=(255, 255, 255), spacing=16)
path = tempfile.mktemp(suffix=".jpg")
img.save(path, quality=92)
media = cl.photo_upload_to_story(path, caption=caption[:2200])
print("ACA_IG_STORY_OK", getattr(media, "pk", media))
"""
    ).strip()
    b64 = base64.b64encode(py.encode("utf-8")).decode("ascii")
    inner = f"import base64; exec(base64.b64decode({b64!r}).decode())"
    env = (
        f"ACA_IG_USER={shlex.quote(user)} "
        f"ACA_IG_PASS={shlex.quote(pwd)} "
        f"ACA_IG_TEXT={shlex.quote(text)} "
    )
    cmd = f"{env}python3 -c {shlex.quote(inner)}"
    raw = run_shell(cmd, ".", options)
    if raw.startswith("ERROR:"):
        return raw
    if "exit_code=0" not in raw:
        return tool_result(False, f"انتشار استوری ناموفق:\n{raw}")
    if "ACA_IG_STORY_OK" not in raw:
        return tool_result(
            False,
            "خروجی سرور تأیید انتشار استوری نداشت — instagrapi/Pillow را روی همان محیط "
            "اجرای run_shell نصب کنید:\n" + raw,
        )
    return tool_result(True, "استوری در اینستاگرام منتشر شد.\n" + raw.split("OK:", 1)[-1].strip())


def run_shell(command: str, cwd: str, options: AgentOptions) -> str:
    if not options.allow_shell:
        return tool_result(
            False,
            "Shell disabled by user (allow_shell=false).",
        )
    from .security import shell_command_allowed

    blocked = shell_command_allowed(command)
    if blocked:
        return tool_result(False, blocked)
    priv = _blocked_private(options, cwd or ".")
    if priv:
        return priv
    io = _io(options)
    try:
        cwd_rel = io.resolve_rel(cwd or ".")
        if not io.is_dir(cwd_rel):
            return tool_result(False, f"Not a directory: {cwd}")
        code, out, _err = io.run_shell(command, cwd_rel, settings.AGENT_COMMAND_TIMEOUT)
        summary = f"exit_code={code}\ncwd={cwd_rel}\n{out}"
        return tool_result(code == 0, summary)
    except WorkspaceError as e:
        return tool_result(False, str(e))
    except subprocess.TimeoutExpired:
        return tool_result(False, f"Command timed out after {settings.AGENT_COMMAND_TIMEOUT}s")
    except OSError as e:
        return tool_result(False, str(e))
