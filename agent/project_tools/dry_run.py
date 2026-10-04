"""اجرای آزمایشی ابزار قبل از نوشتن روی دیسک."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

from agent.options import AgentOptions

from .template import build_module_source
from .validator import ToolValidationError


def dry_run_tool_body(
    source_body: str,
    test_arguments: dict[str, Any] | None,
    options: AgentOptions,
) -> None:
    full_source = build_module_source(source_body)
    mod_name = f"aca_dry_run_{uuid.uuid4().hex}"
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            encoding="utf-8",
            delete=False,
        ) as fh:
            fh.write(full_source)
            tmp_path = Path(fh.name)
        spec = importlib.util.spec_from_file_location(mod_name, tmp_path)
        if spec is None or spec.loader is None:
            raise ToolValidationError("بارگذاری آزمایشی ابزار ناموفق بود")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = mod
        spec.loader.exec_module(mod)
        run_fn = getattr(mod, "run", None)
        if not callable(run_fn):
            raise ToolValidationError("تابع run در ماژول آزمایشی پیدا نشد")
        args = dict(test_arguments if test_arguments is not None else {})
        try:
            out = run_fn(args, options)
        except Exception as exc:
            raise ToolValidationError(
                f"اجرای آزمایشی run خطا داد: {exc} — "
                "برای خواندن فایل از read_workspace_text(path, options) استفاده کنید "
                "(نه read_file با آرگومان‌های ناقص)."
            ) from exc
        if not isinstance(out, str):
            raise ToolValidationError(
                "run باید str برگرداند — همیشه return tool_result(True/False, ...) استفاده کنید"
            )
        if test_arguments is not None and out.startswith("ERROR:"):
            raise ToolValidationError(f"تست اولیه ناموفق: {out[:800]}")
    finally:
        sys.modules.pop(mod_name, None)
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
