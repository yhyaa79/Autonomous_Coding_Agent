"""اعتبارسنجی ابزار سفارشی پروژه (امنیت پایه)."""

import ast
import re

TOOL_ID_RE = re.compile(r"^[a-z][a-z0-9_]{2,48}$")

FORBIDDEN_NAMES = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "__import__",
        "open",
        "breakpoint",
        "input",
    }
)

FORBIDDEN_MODULES = frozenset(
    {
        "os",
        "sys",
        "subprocess",
        "socket",
        "shutil",
        "pickle",
        "ctypes",
        "multiprocessing",
        "importlib",
        "builtins",
    }
)

ALLOWED_MODULES = frozenset(
    {
        "json",
        "re",
        "math",
        "datetime",
        "pathlib",
        "typing",
        "decimal",
        "hashlib",
        "urllib",
        "paramiko",
    }
)


class ToolValidationError(ValueError):
    pass


def validate_tool_id(tool_id: str) -> str:
    tid = (tool_id or "").strip()
    if not TOOL_ID_RE.match(tid):
        raise ToolValidationError(
            "tool_id باید با حرف کوچک شروع شود و فقط a-z0-9_ (۳–۴۹ کاراکتر)"
        )
    if tid.startswith("aca_"):
        raise ToolValidationError("پیشوند aca_ برای ابزارهای سیستمی است")
    return tid


def validate_parameters_schema(schema: dict) -> dict:
    if not isinstance(schema, dict):
        raise ToolValidationError("parameters باید object JSON Schema باشد")
    if schema.get("type") != "object":
        schema = {"type": "object", "properties": schema.get("properties") or {}, "required": schema.get("required") or []}
    props = schema.get("properties")
    if props is not None and not isinstance(props, dict):
        raise ToolValidationError("properties نامعتبر")
    req = schema.get("required")
    if req is not None and not isinstance(req, list):
        raise ToolValidationError("required باید آرایه باشد")
    return schema


def _find_run_function(tree: ast.AST) -> ast.FunctionDef | None:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "run":
            return node
    return None


def _dedent_block(segment: str) -> str:
    lines = segment.splitlines()
    indents = [len(line) - len(line.lstrip(" ")) for line in lines if line.strip()]
    if not indents:
        return segment.strip()
    min_indent = min(indents)
    out: list[str] = []
    for line in lines:
        if not line.strip():
            out.append("")
            continue
        if len(line) >= min_indent and line[:min_indent].isspace():
            out.append(line[min_indent:])
        else:
            out.append(line.lstrip())
    return "\n".join(out).strip()


def _source_segment(body: str, node: ast.AST) -> str:
    seg = ast.get_source_segment(body, node)
    if seg:
        return seg.strip()
    if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
        return ""
    lines = body.splitlines()
    start = node.lineno - 1
    end = node.end_lineno
    if start < 0 or end > len(lines):
        return ""
    return "\n".join(lines[start:end]).strip()


def _module_prefix_before_run(body: str, tree: ast.Module, run_func: ast.FunctionDef) -> str:
    parts: list[str] = []
    for node in tree.body:
        if node is run_func:
            break
        seg = _source_segment(body, node)
        if seg:
            parts.append(seg)
    return "\n".join(parts).strip()


def normalize_source_body(raw: str) -> str:
    """بدنهٔ run را از خروجی مدل (fence، def run کامل، …) استخراج می‌کند."""
    body = (raw or "").strip()
    if not body:
        return body
    if body.startswith("```"):
        lines = body.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        body = "\n".join(lines).strip()
    try:
        tree = ast.parse(body)
    except SyntaxError:
        return body
    if not isinstance(tree, ast.Module):
        return body
    run_func = _find_run_function(tree)
    if run_func is None or not run_func.body:
        return body
    src_lines = body.splitlines()
    start = run_func.body[0].lineno - 1
    end = run_func.body[-1].end_lineno
    if start < 0 or end > len(src_lines):
        return body
    inner = "\n".join(src_lines[start:end])
    peeled = _dedent_block(inner)
    prefix = _module_prefix_before_run(body, tree, run_func)
    if prefix and peeled:
        return f"{prefix}\n{peeled}"
    return peeled or body


def _is_ast_descendant(node: ast.AST, ancestor: ast.AST) -> bool:
    for child in ast.iter_child_nodes(ancestor):
        if child is node:
            return True
        if _is_ast_descendant(node, child):
            return True
    return False


def _has_return_outside_nested_functions(func: ast.FunctionDef) -> bool:
    """حداقل یک return در بدنهٔ run (شامل try/except/for) — نه داخل تابع تودرتو."""
    nested_funcs = [
        n
        for n in ast.walk(func)
        if isinstance(n, ast.FunctionDef) and n is not func
    ]
    for node in ast.walk(func):
        if not isinstance(node, ast.Return):
            continue
        if any(_is_ast_descendant(node, nested) for nested in nested_funcs):
            continue
        return True
    return False


def _validate_run_function_shape(run_func: ast.FunctionDef) -> None:
    for child in run_func.body:
        if isinstance(child, ast.FunctionDef) and child.name == "run":
            raise ToolValidationError(
                "تابع run تودرتو مجاز نیست — مستقیماً return tool_result(...) بنویسید؛ "
                "def run دیگر داخل بدنه نگذارید."
            )
    if not _has_return_outside_nested_functions(run_func):
        raise ToolValidationError(
            "بدنهٔ run باید حداقل یک return tool_result(...) داشته باشد "
            "(مثلاً در try/except یا انتهای بدنه) — return فقط داخل تابع داخلی کافی نیست."
        )


def _check_common_run_mistakes(tree: ast.AST) -> None:
    """اشتباهات رایج مدل (مثلاً parameters به‌جای arguments)."""
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "parameters"
        ):
            raise ToolValidationError(
                "در source_body ورودی ابزار با arguments در دسترس است — "
                "parameters.get(...) اشتباه است (parameters فقط نام فیلد JSON "
                "در create_project_tool است). مثال: arguments.get('username')"
            )
        if isinstance(node, ast.Call):
            func_name: str | None = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            if func_name == "read_workspace_text" and len(node.args) >= 2:
                second = node.args[1]
                if isinstance(second, ast.Dict):
                    raise ToolValidationError(
                        "read_workspace_text(path, options) — آرگومان دوم باید "
                        "متغیر options باشد، نه dict خالی."
                    )


def _check_ast_tree(tree: ast.AST) -> None:
    _check_common_run_mistakes(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            raise ToolValidationError(f"استفاده از {node.id} مجاز نیست")
        if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_NAMES:
            raise ToolValidationError(f"استفاده از .{node.attr} مجاز نیست")
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                if mod in FORBIDDEN_MODULES:
                    raise ToolValidationError(f"import {mod} مجاز نیست")
                if mod not in ALLOWED_MODULES and not alias.name.startswith("agent.tool_impl"):
                    hint = ""
                    if mod == "requests":
                        hint = (
                            " — برای استوری اینستاگرام instagram_post_story یا "
                            "post_instagram_text_story از agent.tool_impl؛ "
                            "import requests مجاز نیست."
                        )
                    raise ToolValidationError(f"import {alias.name} مجاز نیست{hint}")
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.split(".")[0] in FORBIDDEN_MODULES:
                raise ToolValidationError(f"import from {node.module} مجاز نیست")
            if mod and mod.split(".")[0] not in ALLOWED_MODULES and not mod.startswith(
                ("agent.tool_impl", "agent.options")
            ):
                raise ToolValidationError(f"import from {node.module} مجاز نیست")


def _tool_targets_instagram_publish(
    tool_id: str,
    description: str,
    parameters: dict | None,
) -> bool:
    tid = (tool_id or "").lower()
    desc = (description or "").lower()
    if "instagram" in tid or "insta_" in tid:
        return True
    if any(k in desc for k in ("instagram", "اینستاگرام", "insta")):
        return True
    if "استوری" in (description or "") and "اینستا" in (description or ""):
        return True
    props = (parameters or {}).get("properties") if isinstance(parameters, dict) else None
    if isinstance(props, dict):
        keys = {str(k).lower() for k in props}
        if "story_text" in keys and ("username" in keys or "password" in keys):
            return True
    return False


_INSTAGRAM_PUBLISH_MARKERS = (
    "post_instagram_text_story",
    "run_shell",
    "exec_command",
    "photo_upload_to_story",
    "instagrapi",
)


def validate_instagram_publish_body(
    source_body: str,
    tool_id: str = "",
    description: str = "",
    parameters: dict | None = None,
) -> None:
    """جلوگیری از ابزار جعلی که فقط پیام موفقیت برمی‌گرداند."""
    if not _tool_targets_instagram_publish(tool_id, description, parameters):
        return
    body = normalize_source_body(source_body)
    lowered = body.lower()
    if "api.instagram.com" in lowered:
        raise ToolValidationError(
            "API عمومی api.instagram.com برای استوری معتبر نیست — "
            "از agent.tool_impl.post_instagram_text_story یا ابزار instagram_post_story استفاده کنید."
        )
    if any(marker in body for marker in _INSTAGRAM_PUBLISH_MARKERS):
        return
    if "paramiko" in lowered and "connect" in lowered:
        return
    raise ToolValidationError(
        "ابزار انتشار اینستاگرام باید واقعاً استوری را منتشر کند — "
        "return tool_result(True, 'استوری ارسال شد') بدون فراخوانی مجاز نیست. "
        "در source_body: from agent.tool_impl import post_instagram_text_story و "
        "return post_instagram_text_story(username, password, story_text, options) "
        "یا ابزار سیستمی instagram_post_story را صدا بزنید (نه requests و نه API جعلی)."
    )


def validate_run_body(source_body: str) -> None:
    body = normalize_source_body(source_body)
    if not body:
        raise ToolValidationError("source_body خالی است")
    if len(body) > 10000:
        raise ToolValidationError("source_body بیش از حد بزرگ است")
    indented = "\n".join("    " + line for line in body.splitlines())
    # از f-string استفاده نکنید — بدنهٔ ابزار ممکن است { } داشته باشد (f-string، dict و …).
    code = "def run(arguments, options):\n" + indented + "\n"
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ToolValidationError(f"خطای syntax در body: {e}") from e
    _check_ast_tree(tree)
    run_func = _find_run_function(tree)
    if run_func is None:
        raise ToolValidationError("تابع run در body پیدا نشد")
    _validate_run_function_shape(run_func)


def validate_python_source(source: str) -> None:
    code = (source or "").strip()
    if not code:
        raise ToolValidationError("source_code خالی است")
    if len(code) > 12000:
        raise ToolValidationError("source_code بیش از حد بزرگ است")
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ToolValidationError(f"خطای syntax: {e}") from e
    has_run = any(isinstance(n, ast.FunctionDef) and n.name == "run" for n in ast.walk(tree))
    if not has_run:
        raise ToolValidationError("تابع run الزامی است")
    _check_ast_tree(tree)
