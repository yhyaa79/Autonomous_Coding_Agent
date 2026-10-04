import json
from collections.abc import Iterator
from typing import Any

from django.conf import settings
from openai import APIError, AuthenticationError, OpenAI, RateLimitError

from agent.message_budget import (
    assistant_tool_message_for_api,
    prepare_messages_for_chat_completion,
    trim_history_message_content,
)
from .debug_recovery import DebugTracker
from .tool_create_budget import reset_tool_create_budget
from .focus_infer import infer_focus_scope
from .history import trim_chat_history
from .options import AgentOptions
from .scope import normalize_scope_paths
from .phase_context import set_phase_collector
from .phases import phase_event, phase_for_tool
from .registry import ensure_agents_loaded, get_agent
from .thinking import run_thinking_phase
from .tool_api import dispatch_tool, parse_tool_args, tool_definitions_for_agent
from .permission_gate import (
    create_permission_request,
    tool_needs_shell,
    tool_needs_write,
    wait_permission,
)
from .user_input_gate import (
    assistant_text_promised_user_form,
    default_ssh_ask_user_args,
    iter_ask_user,
    redact_ask_user_step,
    tool_steps_include_ask_user,
)
from .run_control import is_cancelled
from .tool_impl import tool_result


def _current_time_context() -> str:
    from zoneinfo import ZoneInfo

    from django.utils import timezone

    tz = ZoneInfo("Asia/Tehran")
    now = timezone.localtime(timezone.now(), timezone=tz)
    return (
        f"Current date/time (Asia/Tehran): {now.strftime('%Y-%m-%d %H:%M:%S %Z')} "
        f"(ISO {now.isoformat(timespec='seconds')}). "
        "Use this clock for schedule_job run_at, cron, and when the user says «امروز» or «now»."
    )


def _agent_error(
    code: str,
    reply: str,
    history: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    return {
        "reply": reply,
        "error": code,
        "tool_steps": [],
        "history": list(history or []),
    }


def _scope_system_message(options: AgentOptions) -> str:
    from .workspace_io import get_workspace_io

    ws = get_workspace_io(options).root_display()
    scopes = options.effective_scope()
    lines = [
        f"Project root: {ws}",
        _current_time_context(),
        "Cost rule: never load the whole repo into context — search_code, glob_files, then read_file slices.",
        "For large files: use read_file with start_line/end_line (≤80 lines per read). "
        "Prefer apply_patch with small unique old_string snippets; never paste entire file in tool args.",
    ]
    if getattr(options, "remote_session", None) is not None:
        lines.append(
            "REMOTE SSH: read/write/shell tools execute on the linked server — "
            "default workspace is the project path on that host; absolute paths "
            "work only when server-wide file access is enabled for the project."
        )
    else:
        lines.append(
            "No remote SSH linked: never run ssh, scp, or sshpass on the local worker. "
            "Use ask_user for connection details and tell the user to save server settings "
            "in the project panel, or use run_shell only after remote SSH is configured."
        )
    lines.append(
        "Secrets: use ask_user with password fields — do not ask for passwords in plain chat. "
        "The UI form ONLY appears when you call ask_user; never tell the user to use a form "
        "without calling that tool in the same turn. "
        "If the user message contains [فرم اتصال سرور] with JSON, parse values and proceed."
    )
    if options.has_user_scope() and scopes:
        lines.append("FOCUS SCOPE (content edit/read — user-defined):")
        lines.extend(f"  - {s}" for s in scopes)
        lines.append(
            "You may always explore the whole repo (project_tree, list_directory, glob_files, "
            "search_code paths) to see what files exist and avoid duplicates."
        )
        lines.append(
            "read_file / write_file / apply_patch only inside FOCUS paths. "
            "search_code may match anywhere but hides line text outside focus."
        )
        lines.append(
            "To edit outside focus, ask the user to add paths to focus first."
        )
    elif scopes:
        lines.append(
            "FOCUS HINT (auto-inferred — prefer these paths; full project access including content):"
        )
        lines.extend(f"  - {s}" for s in scopes)
    else:
        lines.append(
            "Scope: full project — explore and read/write anywhere (use targeted tools)."
        )
    if options.scope_note.strip():
        lines.append(f"User focus note: {options.scope_note.strip()}")
    mem = _project_memory_snippet(options)
    if mem:
        lines.append(mem)
    guide = _resource_platform_guide()
    if guide:
        lines.append(guide)
    resources = _conversation_resources_snippet(options)
    if resources:
        lines.append(resources)
    always_ctx = _always_context_snippet(options)
    if always_ctx:
        lines.append(always_ctx)
    denied = normalize_scope_paths(options.denied_content_paths)
    if denied:
        lines.append(
            "DENIED CONTENT (never read_file/write/patch these paths; names may appear in tree):"
        )
        lines.extend(f"  - {s}" for s in denied)
    return "\n".join(lines)


def _always_context_snippet(options: AgentOptions) -> str:
    from agent.project_context_files import always_context_snippet
    from agent.scope import normalize_scope_paths

    paths = normalize_scope_paths(options.always_context_paths)
    if not paths:
        return ""
    return always_context_snippet(options.workspace_path(), paths)


def _conversation_resources_snippet(options: AgentOptions) -> str:
    from projects.shared_tools import conversation_resource_context

    if not options.conversation_id:
        return ""
    try:
        text = conversation_resource_context(options.conversation_id)
    except Exception:
        return ""
    cap = int(getattr(settings, "AGENT_RESOURCE_SNIPPET_CHARS", 12000))
    if len(text) > cap:
        text = text[:cap] + "\n...(truncated)"
    return text


def _patch_scope_system_message(messages: list[dict[str, Any]], options: AgentOptions) -> None:
    content = _scope_system_message(options)
    for i, m in enumerate(messages):
        if m.get("role") == "system" and str(m.get("content", "")).startswith("Project root:"):
            messages[i] = {"role": "system", "content": content}
            return
    messages.insert(1, {"role": "system", "content": content})


def _resource_platform_guide() -> str:
    try:
        from projects.resource_tags import resource_agent_guide_snippet

        return resource_agent_guide_snippet()
    except Exception:
        return ""


def _growth_hub_snippet(options: AgentOptions) -> str:
    if not options.project_id:
        return ""
    try:
        from projects.growth_hub import get_or_create_hub, hub_public_dict

        from projects.models import Project

        project = Project.objects.filter(pk=options.project_id).first()
        if project is None:
            return ""
        hub = get_or_create_hub(project)
        data = hub_public_dict(hub)
    except Exception:
        return ""
    stage = data.get("lifecycle_stage") or "build"
    url = data.get("production_url") or "—"
    m_done = sum(1 for t in data.get("maintenance_tasks") or [] if t.get("done"))
    m_total = len(data.get("maintenance_tasks") or [])
    g_done = sum(1 for t in data.get("marketing_tasks") or [] if t.get("done"))
    g_total = len(data.get("marketing_tasks") or [])
    enabled_ch = [
        cid
        for cid, st in (data.get("channels") or {}).items()
        if isinstance(st, dict) and st.get("enabled")
    ]
    lines = [
        "Growth hub (post-launch):",
        f"  lifecycle_stage={stage} · production_url={url}",
        f"  maintenance checklist: {m_done}/{m_total} done",
        f"  marketing checklist: {g_done}/{g_total} done",
    ]
    if enabled_ch:
        lines.append(f"  enabled channels: {', '.join(enabled_ch[:8])}")
    lines.append("  Use update_growth_hub to persist progress.")
    return "\n".join(lines)


def _project_memory_snippet(options: AgentOptions) -> str:
    from agent.project_data import read_project_memory

    text = read_project_memory(options.project_id)
    if not text:
        return ""
    cap = int(getattr(settings, "AGENT_MEMORY_SNIPPET_CHARS", 2500))
    if len(text) > cap:
        text = text[:cap] + "\n...(truncated)"
    return f"Project memory:\n{text}"


def _inject_thinking(
    client: OpenAI,
    messages: list[dict[str, Any]],
    user_message: str,
    options: AgentOptions,
) -> tuple[str, list[dict[str, Any]]]:
    if not options.enable_thinking:
        return "", messages
    base = messages[:-1] if messages and messages[-1].get("role") == "user" else list(messages)
    try:
        thinking_text = run_thinking_phase(client, base, user_message, options)
    except (AuthenticationError, RateLimitError, APIError):
        return "", messages
    if not thinking_text:
        return "", messages
    enriched = list(messages)
    insert_at = len(enriched) - 1 if enriched and enriched[-1].get("role") == "user" else len(enriched)
    enriched.insert(
        insert_at,
        {
            "role": "system",
            "content": f"[فاز thinking — تحلیل قبل از ابزار]\n{thinking_text}",
        },
    )
    return thinking_text, enriched


def _apply_auto_focus(
    client: OpenAI,
    messages: list[dict[str, Any]],
    user_message: str,
    options: AgentOptions,
    thinking_text: str,
) -> list[str]:
    if options.has_user_scope():
        return []
    paths = infer_focus_scope(client, user_message, options, thinking_text=thinking_text)
    options.inferred_scope_paths = paths
    _patch_scope_system_message(messages, options)
    return paths


def _system_prompt(options: AgentOptions) -> str:
    ensure_agents_loaded()
    return get_agent(options.agent_type).system_prompt


def _build_messages(
    user_message: str,
    history: list[dict[str, Any]] | None,
    options: AgentOptions,
) -> list[dict[str, Any]]:
    max_turns = getattr(settings, "AGENT_MAX_HISTORY_TURNS", 20)
    trimmed = trim_chat_history(history or [], max_turns)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _system_prompt(options)},
        {"role": "system", "content": _scope_system_message(options)},
    ]
    for item in trimmed:
        role = item.get("role")
        content = item.get("content", "")
        if role in ("user", "assistant") and content:
            if role == "assistant":
                content = trim_history_message_content(str(content))
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})
    return messages


def _get_client(opts: AgentOptions) -> OpenAI | None:
    timeout = float(getattr(settings, "AGENT_LLM_TIMEOUT", 300.0))
    if opts.llm_api_key:
        return OpenAI(
            api_key=opts.llm_api_key,
            base_url=(opts.llm_base_url or "").strip() or settings.GAPGPT_BASE_URL,
            timeout=timeout,
        )
    if not settings.GAPGPT_API_KEY:
        return None
    return OpenAI(
        api_key=settings.GAPGPT_API_KEY,
        base_url=settings.GAPGPT_BASE_URL,
        timeout=timeout,
    )


def _trim_tool_message_for_model(content: str) -> str:
    from agent.message_budget import trim_text_content

    max_len = int(getattr(settings, "AGENT_MAX_TOOL_RESULT_CHARS", 8000))
    return trim_text_content(content, max_len)


def _call_model(
    client: OpenAI,
    messages: list[dict[str, Any]],
    model: str,
    options: AgentOptions,
):
    tools = tool_definitions_for_agent(options.agent_type, options)
    last_error: Exception | None = None
    for aggressive in (False, True):
        payload = prepare_messages_for_chat_completion(
            messages, model, aggressive=aggressive
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=payload,
                tools=tools,
                tool_choice="auto",
                parallel_tool_calls=False,
                temperature=0.2,
            )
            tracker = options.usage_tracker
            if tracker is not None:
                completion = ""
                if response.choices:
                    completion = response.choices[0].message.content or ""
                tracker.add_completion(
                    model,
                    response,
                    messages_for_estimate=payload,
                    completion_text=completion,
                )
            return response
        except APIError as exc:
            last_error = exc
            status = getattr(exc, "status_code", None)
            if status == 400 and not aggressive:
                continue
            raise
    if last_error:
        raise last_error
    raise RuntimeError("model call failed without response")


def _maybe_request_permission(
    tool_name: str,
    args: dict[str, Any],
    opts: AgentOptions,
) -> Iterator[dict[str, Any]]:
    """اگر نوشتن/shell خاموش است، از کاربر اجازه بگیر (بلوک تا پاسخ UI)."""
    need_write = tool_needs_write(tool_name, args) and not opts.allow_write
    need_shell = tool_needs_shell(tool_name) and not opts.allow_shell
    if not need_write and not need_shell:
        return
    kind = "allow_write" if need_write else "allow_shell"
    request_id = create_permission_request(kind, tool_name, args, run_id=opts.run_id)
    yield {
        "type": "permission_request",
        "request_id": request_id,
        "kind": kind,
        "tool": tool_name,
        "args": args,
        "message": (
            "ایجنت می‌خواهد فایل بنویسد یا ویرایش کند."
            if kind == "allow_write"
            else "ایجنت می‌خواهد دستور shell اجرا کند."
        ),
    }
    approved = wait_permission(request_id, run_id=opts.run_id)
    if approved is True:
        if kind == "allow_write":
            opts.allow_write = True
        else:
            opts.allow_shell = True
        yield {
            "type": "permission_resolved",
            "request_id": request_id,
            "kind": kind,
            "approved": True,
        }
    elif approved is False:
        yield {
            "type": "permission_resolved",
            "request_id": request_id,
            "kind": kind,
            "approved": False,
        }
    else:
        yield {
            "type": "permission_resolved",
            "request_id": request_id,
            "kind": kind,
            "approved": False,
            "timed_out": True,
        }


def _permission_denied_result(kind: str, tool_name: str) -> str:
    if kind == "allow_write":
        return tool_result(
            False,
            "User denied write permission. Do not retry write tools; explain or suggest enabling write.",
        )
    return tool_result(
        False,
        "User denied shell permission. Do not retry shell; suggest another approach.",
    )


def _handle_api_error(exc: Exception, history: list[dict[str, Any]] | None) -> dict[str, Any]:
    if isinstance(exc, AuthenticationError):
        return _agent_error(
            "invalid_api_key",
            "کلید گپ‌جی‌پی‌تی نامعتبر است. GAPGPT_API_KEY و GAPGPT_BASE_URL را بررسی کنید.",
            history,
        )
    if isinstance(exc, RateLimitError):
        return _agent_error(
            "rate_limit",
            "محدودیت نرخ API. کمی صبر کنید یا اعتبار حساب را بررسی کنید.",
            history,
        )
    if isinstance(exc, APIError):
        msg = str(getattr(exc, "message", None) or exc)
        if getattr(exc, "status_code", None) == 400 or "400" in msg:
            return _agent_error(
                "openai_api_error",
                "درخواست به API خیلی بزرگ یا نامعتبر بود (۴۰۰). "
                "برای فایل بزرگ از read_file تکه‌ای و apply_patch کوچک استفاده کنید؛ "
                "یا مکالمهٔ جدید بسازید. جزئیات: "
                + msg,
                history,
            )
        return _agent_error("openai_api_error", f"خطا از API: {msg}", history)
    if isinstance(exc, TimeoutError):
        return _agent_error(
            "llm_timeout",
            "زمان پاسخ مدل تمام شد. دوباره تلاش کنید یا مدل دیگری انتخاب کنید.",
            history,
        )
    msg = str(exc).lower()
    if "timed out" in msg or "timeout" in msg:
        return _agent_error(
            "llm_timeout",
            "زمان پاسخ مدل تمام شد. دوباره تلاش کنید یا مدل دیگری انتخاب کنید.",
            history,
        )
    raise exc


def _agent_run_events(
    user_message: str,
    history: list[dict[str, Any]] | None,
    opts: AgentOptions,
) -> Iterator[dict[str, Any]]:
    from .workspace_io import close_remote_session

    client = _get_client(opts)
    if client is None:
        yield {
            "type": "error",
            "error": "missing_api_key",
            "reply": "کلید API برای این مدل تنظیم نشده است.",
        }
        return

    phase_log: list[dict[str, Any]] = []
    thinking_text = ""
    try:
        yield from _agent_run_events_body(
            user_message,
            history,
            opts,
            client,
            phase_log,
        )
    except Exception as exc:
        try:
            err = _handle_api_error(exc, history)
        except Exception:
            err = _agent_error(
                "internal",
                f"خطای غیرمنتظره در اجرای ایجنت: {exc}",
                history,
            )
        yield {"type": "error", "error": err.get("error"), "reply": err.get("reply")}
    finally:
        set_phase_collector(None)
        close_remote_session(opts)


def _agent_run_events_body(
    user_message: str,
    history: list[dict[str, Any]] | None,
    opts: AgentOptions,
    client: OpenAI,
    phase_log: list[dict[str, Any]],
) -> Iterator[dict[str, Any]]:
    messages = _build_messages(user_message, history, opts)

    ev = phase_event("receive")
    phase_log.append(ev)
    yield ev

    if opts.enable_thinking:
        ev = phase_event("thinking")
        phase_log.append(ev)
        yield ev
        thinking_text, messages = _inject_thinking(client, messages, user_message, opts)
        if thinking_text:
            yield {"type": "thinking", "content": thinking_text}
    else:
        thinking_text = ""

    if not opts.has_user_scope():
        ev = phase_event("focus_auto", "در حال تحلیل ساختار پروژه…")
        phase_log.append(ev)
        yield ev
        inferred = _apply_auto_focus(client, messages, user_message, opts, thinking_text)
        detail = "، ".join(inferred) if inferred else "بدون محدودیت مشخص (کل پروژه)"
        yield {
            "type": "focus_inferred",
            "paths": inferred,
            "detail": detail,
        }
        ev = phase_event("focus_auto", detail, paths=inferred)
        phase_log.append(ev)
        yield ev

    model = opts.model or settings.GAPGPT_MODEL
    max_rounds = opts.max_tool_rounds or settings.AGENT_MAX_TOOL_ROUNDS
    tool_steps: list[dict[str, Any]] = []
    recent_failures: list[dict[str, Any]] = []
    final_reply = ""
    reset_tool_create_budget()
    debug_tracker = DebugTracker(
        project_id=opts.project_id,
        workspace=opts.workspace_path(),
    )
    nested_phases: list[dict[str, Any]] = []

    def _collect_phase(ev: dict[str, Any]) -> None:
        nested_phases.append(ev)

    set_phase_collector(_collect_phase)

    stopped_by_user = False
    stopped_by_escalation = False

    for round_idx in range(max_rounds):
        if is_cancelled(opts.run_id):
            stopped_by_user = True
            final_reply = "(کار توسط کاربر متوقف شد.)"
            break
        ev = phase_event("model_plan", f"دور {round_idx + 1}")
        phase_log.append(ev)
        yield ev
        try:
            response = _call_model(client, messages, model, opts)
        except Exception as exc:
            try:
                err = _handle_api_error(exc, history)
            except Exception:
                err = _agent_error(
                    "internal",
                    f"خطا در فراخوانی مدل: {exc}",
                    history,
                )
            yield {"type": "error", "error": err.get("error"), "reply": err.get("reply")}
            return

        msg = response.choices[0].message
        if msg.tool_calls:
            messages.append(assistant_tool_message_for_api(msg))
            for tc in msg.tool_calls:
                fn = tc.function
                args = parse_tool_args(fn.arguments)
                pev = phase_for_tool(fn.name, args)
                phase_log.append(pev)
                yield pev
                yield {"type": "tool_start", "tool": fn.name, "args": args}
                if is_cancelled(opts.run_id):
                    stopped_by_user = True
                    final_reply = "(کار توسط کاربر متوقف شد.)"
                    break
                if stopped_by_user:
                    break
                permission_kind: str | None = None
                if tool_needs_write(fn.name, args) and not opts.allow_write:
                    permission_kind = "allow_write"
                elif tool_needs_shell(fn.name) and not opts.allow_shell:
                    permission_kind = "allow_shell"
                if permission_kind:
                    for pe in _maybe_request_permission(fn.name, args, opts):
                        yield pe
                    if permission_kind == "allow_write" and not opts.allow_write:
                        result = _permission_denied_result("allow_write", fn.name)
                    elif permission_kind == "allow_shell" and not opts.allow_shell:
                        result = _permission_denied_result("allow_shell", fn.name)
                    else:
                        nested_phases.clear()
                        try:
                            result = dispatch_tool(fn.name, args, opts)
                        except Exception as exc:
                            result = tool_result(
                                False,
                                f"خطای داخلی ابزار {fn.name}: {exc}",
                            )
                elif fn.name == "ask_user":
                    nested_phases.clear()
                    result = yield from iter_ask_user(args, run_id=opts.run_id)
                    if not isinstance(result, str):
                        result = tool_result(False, "ask_user بدون نتیجه تمام شد.")
                else:
                    nested_phases.clear()
                    try:
                        result = dispatch_tool(fn.name, args, opts)
                    except Exception as exc:
                        result = tool_result(
                            False,
                            f"خطای داخلی ابزار {fn.name}: {exc}",
                        )
                for np in nested_phases:
                    phase_log.append(np)
                    yield np
                step = {
                    "round": round_idx + 1,
                    "tool": fn.name,
                    "args": args,
                    "result": result,
                }
                step = redact_ask_user_step(step)
                tool_steps.append(step)
                yield {"type": "tool_end", **step}
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": _trim_tool_message_for_model(result),
                    }
                )
                if result.startswith("ERROR:"):
                    recent_failures.append(step)
                    action = debug_tracker.handle_failure(fn.name, result, args)
                    if action == "hint":
                        messages.append(
                            {
                                "role": "system",
                                "content": debug_tracker.build_error_hint(recent_failures),
                            }
                        )
                    elif action == "recover":
                        recovery = debug_tracker.run_recovery_analysis(
                            client,
                            user_message,
                            recent_failures,
                            opts,
                        )
                        for np in nested_phases:
                            phase_log.append(np)
                            yield np
                        messages.append(
                            {
                                "role": "system",
                                "content": f"[ACA Debug — راه‌حل جایگزین]\n{recovery}",
                            }
                        )
                    elif action == "escalate":
                        final_reply = debug_tracker.run_user_escalation(
                            client,
                            user_message,
                            recent_failures,
                            opts,
                        )
                        for np in nested_phases:
                            phase_log.append(np)
                            yield np
                        stopped_by_escalation = True
                        break
            if stopped_by_user or stopped_by_escalation:
                break
            continue

        ev = phase_event("compose")
        phase_log.append(ev)
        yield ev
        reply_text = msg.content or ""
        if (
            not tool_steps_include_ask_user(tool_steps)
            and assistant_text_promised_user_form(reply_text)
        ):
            auto_args = default_ssh_ask_user_args(reply_text)
            yield {"type": "tool_start", "tool": "ask_user", "args": auto_args}
            ask_result = yield from iter_ask_user(auto_args, run_id=opts.run_id)
            if not isinstance(ask_result, str):
                ask_result = tool_result(False, "ask_user بدون نتیجه تمام شد.")
            step = {
                "round": round_idx + 1,
                "tool": "ask_user",
                "args": auto_args,
                "result": ask_result,
            }
            step = redact_ask_user_step(step)
            tool_steps.append(step)
            yield {"type": "tool_end", **step}
            messages.append({"role": "assistant", "content": reply_text})
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "[اطلاعات فرم کاربر — از ask_user؛ دوباره درخواست فرم نکن.]\n"
                        + ask_result
                    ),
                }
            )
            if ask_result.startswith("OK:"):
                continue
            final_reply = reply_text
            break
        final_reply = reply_text
        break
    else:
        final_reply = (
            "به حداکثر مراحل ابزار رسیدم. درخواست را تقسیم کنید یا "
            "max_tool_rounds را افزایش دهید."
        )

    new_history = list(history or [])
    new_history.append({"role": "user", "content": user_message})
    new_history.append({"role": "assistant", "content": final_reply})

    ev = phase_event("done")
    phase_log.append(ev)
    yield ev

    usage_payload = opts.usage_tracker.to_dict() if opts.usage_tracker else None

    yield {
        "type": "done",
        "reply": final_reply,
        "thinking": thinking_text,
        "tool_steps": tool_steps,
        "history": new_history,
        "rounds_used": len({s["round"] for s in tool_steps}) if tool_steps else 0,
        "inferred_scope_paths": list(opts.inferred_scope_paths or []),
        "phase_log": phase_log,
        "debug_recoveries": debug_tracker.recovery_count,
        "debug_escalated": debug_tracker.escalated,
        "usage": usage_payload,
        "stopped_by_user": stopped_by_user,
        "stopped_by_escalation": stopped_by_escalation,
    }


def run_agent(
    user_message: str,
    history: list[dict[str, Any]] | None = None,
    options: AgentOptions | None = None,
) -> dict[str, Any]:
    opts = options or AgentOptions()
    if not opts.llm_api_key and not settings.GAPGPT_API_KEY:
        return {
            "reply": "GAPGPT_API_KEY تنظیم نشده. از پنل gapgpt.app کلید بگیرید.",
            "tool_steps": [],
            "history": history or [],
        }

    phase_log: list[dict[str, Any]] = []
    final: dict[str, Any] | None = None
    for event in _agent_run_events(user_message, history, opts):
        if event.get("type") == "phase":
            phase_log.append(event)
        if event.get("type") == "done":
            final = event

    if not final:
        return _agent_error("internal", "پاسخی تولید نشد.", history)

    return {
        "reply": final.get("reply", ""),
        "tool_steps": final.get("tool_steps") or [],
        "thinking": final.get("thinking") or "",
        "history": final.get("history") or [],
        "rounds_used": final.get("rounds_used", 0),
        "inferred_scope_paths": final.get("inferred_scope_paths") or [],
        "phase_log": final.get("phase_log") or phase_log,
        "usage": final.get("usage"),
    }


def run_agent_events(
    user_message: str,
    history: list[dict[str, Any]] | None = None,
    options: AgentOptions | None = None,
) -> Iterator[dict[str, Any]]:
    """رویدادهای SSE: phase, thinking, focus_inferred, tool, done, error."""
    opts = options or AgentOptions()
    if not opts.llm_api_key and not settings.GAPGPT_API_KEY:
        yield {
            "type": "error",
            "error": "missing_api_key",
            "reply": "GAPGPT_API_KEY تنظیم نشده.",
        }
        return

    yield from _agent_run_events(user_message, history, opts)
