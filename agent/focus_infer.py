"""تشخیص خودکار محدودهٔ focus وقتی کاربر scope تعیین نکرده."""

import json
import re
from typing import Any

from django.conf import settings
from openai import OpenAI

from .options import AgentOptions
from .scope import normalize_scope_paths
from .tool_impl import project_tree
from .workspace import resolve_in_workspace


def _parse_paths_json(text: str) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\[[\s\S]*?\]", text)
        if not m:
            return []
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return []
    if not isinstance(data, list):
        return []
    out: list[str] = []
    for item in data:
        if isinstance(item, str) and item.strip():
            out.append(item.strip().replace("\\", "/").strip("/"))
    return normalize_scope_paths(out)


def _validate_paths(paths: list[str], options: AgentOptions) -> list[str]:
    root = options.workspace_path()
    valid: list[str] = []
    for p in paths:
        try:
            target = resolve_in_workspace(root, p)
            if target.exists():
                rel = target.relative_to(root).as_posix()
                if target.is_file():
                    valid.append(rel)
                else:
                    valid.append(rel if rel else p)
        except Exception:
            continue
    return normalize_scope_paths(valid)[: int(getattr(settings, "AGENT_AUTO_FOCUS_MAX_PATHS", 12))]


def infer_focus_scope(
    client: OpenAI,
    user_message: str,
    options: AgentOptions,
    thinking_text: str = "",
) -> list[str]:
    """مسیرهای نسبی پوشه/فایل برای محدود کردن ابزارها در این درخواست."""
    if options.has_user_scope():
        return []

    tree_preview = project_tree(2, 100, options)
    if tree_preview.startswith("ERROR:"):
        tree_preview = "(tree unavailable)"

    model = getattr(settings, "GAPGPT_FOCUS_MODEL", "") or options.model or settings.GAPGPT_MODEL
    system = (
        "You infer minimal focus paths in a codebase for one user request. "
        "Return ONLY a JSON array of relative path strings (files or directories). "
        "Prefer 2-8 paths: the smallest set that covers the task. "
        "Use paths from the tree when possible. Persian/English requests both ok."
    )
    user = (
        f"Project tree (sample):\n{tree_preview[:6000]}\n\n"
        f"User request:\n{user_message}\n"
    )
    if thinking_text:
        user += f"\nPrior analysis:\n{thinking_text[:2000]}\n"
    user += "\nJSON array only, e.g. [\"src/api\", \"tests/test_foo.py\"]"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.1,
        )
        raw = (response.choices[0].message.content or "").strip()
        tracker = options.usage_tracker
        if tracker is not None:
            tracker.add_completion(
                model,
                response,
                messages_for_estimate=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                completion_text=raw,
            )
    except Exception:
        return []

    paths = _validate_paths(_parse_paths_json(raw), options)
    return paths
