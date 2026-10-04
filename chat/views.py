import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from agent import run_agent
from agent.loop import run_agent_events
from agent.permission_gate import resolve_permission
from agent.user_input_gate import resolve_user_input
from agent.run_control import end_run, request_cancel, try_start_run
from agent.code_changes import file_restore_preview_for_message, undo_preview_for_message
from agent.message_backup import (
    BackupError,
    TurnBackupSession,
    project_backup_lock,
)
from agent.options import AgentOptions
from agent.usage import UsageTracker
from projects.auth_api import billing_user, conversation_owned, require_user
from projects.billing import InsufficientBalance, assert_can_afford, charge_for_usage, wallet_summary
from agent.model_catalog import BYOK_MODEL_ID, default_model_id, is_byok_model_id, models_for_api, resolve_model_id
from projects.user_llm import (
    apply_byok_to_agent_options,
    conversation_uses_byok,
    user_llm_configured,
    user_llm_public_status,
)
from agent.tool_impl import read_file as read_file_tool
from agent.workspace import WorkspaceError, resolve_in_workspace
from agent.workspace_api import build_tree_node
from projects.models import ChatMessage, Conversation
from projects.services import (
    agent_options_for_conversation,
    conversation_context_usage,
    conversation_to_dict,
    save_chat_turn,
    restore_assistant_turn_file,
    undo_assistant_message,
)


def _config_payload(request=None) -> dict:
    import json as _json

    token = getattr(settings, "AGENT_API_TOKEN", "") or ""
    wallet = None
    username = None
    user_llm = None
    if request and request.user.is_authenticated:
        wallet = wallet_summary(request.user)
        username = request.user.get_username()
        user_llm = user_llm_public_status(request.user)
    return {
        "model": settings.GAPGPT_MODEL,
        "default_model": default_model_id(),
        "models": _json.dumps(models_for_api(), ensure_ascii=False),
        "api_base": settings.GAPGPT_BASE_URL,
        "max_tool_rounds": settings.AGENT_MAX_TOOL_ROUNDS,
        "max_history_turns": settings.AGENT_MAX_HISTORY_TURNS,
        "api_token_required": bool(token),
        "auth_required": not token,
        "wallet": _json.dumps(wallet, ensure_ascii=False) if wallet else "null",
        "username": username,
        "user_llm": _json.dumps(user_llm, ensure_ascii=False) if user_llm else "null",
        "byok_model_id": BYOK_MODEL_ID,
    }


def _conversation_from_body(body: dict) -> Conversation:
    cid = body.get("conversation_id")
    if not cid:
        raise ValueError("conversation_id الزامی است — ابتدا پروژه و مکالمه بسازید")
    return get_object_or_404(Conversation, pk=int(cid))


def _prepare_chat(
    request,
    body: dict,
) -> tuple[Conversation, str, list, AgentOptions, UsageTracker]:
    conv = _conversation_from_body(body)
    conv = Conversation.objects.select_related("project").get(pk=conv.pk)
    message = (body.get("message") or "").strip()
    if not message:
        raise ValueError("message is required")
    history = conv.to_history()
    ctx_usage = conversation_context_usage(conv)
    if ctx_usage.get("full"):
        raise ValueError(
            "کانتکست این مکالمه پر شده است — مکالمهٔ جدید بسازید یا تاریخچه را کم کنید."
        )
    opts = agent_options_for_conversation(conv, body.get("options"), user=billing_user(request))
    if opts.conversation_id != conv.id:
        opts.conversation_id = conv.id
    model_pick = (body.get("options") or {}).get("model")
    user = billing_user(request)
    if model_pick:
        mid = resolve_model_id(str(model_pick))
        if is_byok_model_id(mid):
            if not user:
                raise ValueError("استفاده از API شخصی نیاز به ورود دارد")
            if not user_llm_configured(user):
                raise ValueError("ابتدا کلید API شخصی را در تنظیمات ذخیره کنید")
        conv.llm_model = mid
        conv.save(update_fields=["llm_model", "updated_at"])
        opts.model = mid
    apply_byok_to_agent_options(opts, user)
    if not conversation_owned(request, conv):
        raise ValueError("دسترسی به این مکالمه مجاز نیست")
    tracker = UsageTracker()
    opts.usage_tracker = tracker
    return conv, message, history, opts, tracker


def _billing_preflight(request, conv: Conversation, opts: AgentOptions | None = None) -> JsonResponse | None:
    user = billing_user(request)
    if not user:
        return None
    if not conversation_owned(request, conv):
        return JsonResponse({"error": "دسترسی به این مکالمه مجاز نیست"}, status=403)
    if opts and getattr(opts, "billing_exempt", False):
        return None
    if conversation_uses_byok(conv) and user_llm_configured(user):
        return None
    try:
        assert_can_afford(user)
    except InsufficientBalance as exc:
        return JsonResponse(
            {
                "error": "اعتبار کافی نیست",
                "balance_credits": str(exc.balance),
                "required_credits": str(exc.required),
            },
            status=402,
        )
    return None


def _billing_settle_before_save(request, conv, result: dict, opts) -> JsonResponse | None:
    user = billing_user(request)
    if not user:
        return None
    if getattr(opts, "billing_exempt", False):
        return None
    usage = result.get("usage")
    if not usage:
        return None
    try:
        charge_for_usage(
            user,
            conv,
            None,
            usage,
            primary_model=resolve_model_id(conv.llm_model or opts.model),
        )
    except InsufficientBalance as exc:
        return JsonResponse(
            {
                "error": "اعتبار کافی نیست",
                "balance_credits": str(exc.balance),
                "required_credits": str(exc.required),
            },
            status=402,
        )
    return None


def _link_usage_to_assistant(user, conv, assistant) -> None:
    from projects.billing import ChatTokenUsage

    latest = (
        ChatTokenUsage.objects.filter(
            user=user, conversation=conv, assistant_message__isnull=True
        )
        .order_by("-id")
        .first()
    )
    if latest:
        latest.assistant_message = assistant
        latest.save(update_fields=["assistant_message"])


@require_GET
def login_view(request):
    if request.user.is_authenticated:
        return redirect("/")
    return render(request, "chat/login.html")


@csrf_exempt
@require_POST
def login_api(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    user = authenticate(request, username=username, password=password)
    if not user:
        return JsonResponse({"error": "نام کاربری یا رمز اشتباه است"}, status=401)
    login(request, user)
    return JsonResponse({"ok": True, "wallet": wallet_summary(user)})


@require_POST
def logout_api(request):
    logout(request)
    return JsonResponse({"ok": True})


@login_required
@require_GET
def index(request):
    return render(
        request,
        "chat/index.html",
        {
            **_config_payload(request),
            "pending_tool_ref": None,
            "pending_tool_conversation_id": None,
            "pending_tool_project_id": None,
        },
    )


@require_GET
def tool_share_page(request, public_id: str):
    from projects.shared_tools import parse_public_ref

    ref = parse_public_ref(public_id) or public_id.strip().lower()
    return render(
        request,
        "chat/index.html",
        {
            **_config_payload(request),
            "pending_tool_ref": ref,
            "pending_tool_conversation_id": _query_int_id(request.GET.get("conversation_id")),
            "pending_tool_project_id": _query_int_id(request.GET.get("project_id")),
        },
    )


@require_GET
def health(request):
    return JsonResponse(
        {
            "ok": True,
            "has_api_key": bool(settings.GAPGPT_API_KEY),
            **_config_payload(request),
        }
    )


def _query_int_id(raw: str | None) -> int | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.lower() in ("null", "undefined", "none"):
        return None
    try:
        n = int(s)
    except ValueError:
        return None
    return n if n > 0 else None


def _workspace_for_request(request) -> tuple[Path, list[str], list[str]]:
    from projects.user_file_access import user_file_access_lists

    user = billing_user(request)
    _, denied = user_file_access_lists(user)
    cid = _query_int_id(request.GET.get("conversation_id"))
    if cid is not None:
        conv = get_object_or_404(Conversation, pk=cid)
        project = conv.project
        return (
            Path(project.root_path),
            conv.effective_scope(),
            denied,
        )
    pid = _query_int_id(request.GET.get("project_id"))
    if pid is not None:
        from projects.models import Project

        project = get_object_or_404(Project, pk=pid)
        return (
            Path(project.root_path),
            project.effective_default_scope(),
            denied,
        )
    return Path(settings.AGENT_WORKSPACE), [], denied


@require_GET
def workspace_tree(request):
    path = request.GET.get("path", ".")
    depth = int(request.GET.get("depth", "3"))
    root, scopes, _denied = _workspace_for_request(request)
    try:
        tree = build_tree_node(root, path, depth=min(max(depth, 1), 64), scope_paths=scopes)
        return JsonResponse({"tree": tree, "root_path": str(root), "scope_paths": scopes})
    except WorkspaceError as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_GET
def workspace_file(request):
    path = request.GET.get("path", "")
    if not path:
        return JsonResponse({"error": "path required"}, status=400)
    root, scopes, denied = _workspace_for_request(request)
    try:
        resolve_in_workspace(root, path)
        opts = AgentOptions(
            workspace_root=str(root),
            scope_paths=scopes,
            denied_content_paths=denied,
        )
        content = read_file_tool(path, 1, 400, 400, opts)
        return JsonResponse({"path": path, "content": content})
    except WorkspaceError as e:
        return JsonResponse({"error": str(e)}, status=400)


def _json_error(exc: ValueError) -> JsonResponse:
    return JsonResponse({"error": str(exc)}, status=400)


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def _rollback_turn_session(opts) -> None:
    session = getattr(opts, "turn_backup", None)
    if session is None:
        return
    try:
        session.rollback_workspace(opts)
    except Exception:
        pass
    session.discard()


@csrf_exempt
@require_user
@require_POST
def chat_api(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        conv, message, history, opts, tracker = _prepare_chat(request, body)
    except ValueError as e:
        return _json_error(e)

    denied = _billing_preflight(request, conv, opts)
    if denied:
        return denied

    opts.turn_backup = TurnBackupSession(conv)
    from agent.workspace_io import close_remote_session

    try:
        result = run_agent(message, history=history, options=opts)
    except Exception:
        with project_backup_lock(conv.project_id):
            _rollback_turn_session(opts)
        raise
    finally:
        close_remote_session(opts)

    err = result.get("error")
    if err:
        with project_backup_lock(conv.project_id):
            _rollback_turn_session(opts)
        if err == "invalid_api_key":
            return JsonResponse(result, status=401)
        if err in ("rate_limit", "openai_api_error"):
            return JsonResponse(result, status=502)
        return JsonResponse(result)
    user = billing_user(request)
    bill_err = _billing_settle_before_save(request, conv, result, opts) if user else None
    if bill_err:
        with project_backup_lock(conv.project_id):
            _rollback_turn_session(opts)
        return bill_err
    backup = None
    with project_backup_lock(conv.project_id):
        try:
            backup = opts.turn_backup.finalize_record()
        except (BackupError, OSError) as exc:
            _rollback_turn_session(opts)
            return JsonResponse(
                {"error": f"ذخیرهٔ بک‌آپ تغییرات ناموفق بود: {exc}"},
                status=500,
            )
    try:
        assistant = save_chat_turn(
            conv,
            message,
            result.get("reply", ""),
            result.get("tool_steps") or [],
            backup=backup,
            phase_log=result.get("phase_log"),
            thinking=result.get("thinking"),
            usage=result.get("usage"),
        )
    except Exception:
        with project_backup_lock(conv.project_id):
            _rollback_turn_session(opts)
        raise
    if user and result.get("usage"):
        _link_usage_to_assistant(user, conv, assistant)
    result["conversation_id"] = conv.id
    result["assistant_message_id"] = assistant.id
    result["can_undo"] = backup is not None
    result["history"] = conv.to_history()
    if billing_user(request):
        result["wallet"] = wallet_summary(request.user)
    return JsonResponse(result)


@csrf_exempt
@require_user
@require_POST
def chat_stream(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        conv, message, history, opts, tracker = _prepare_chat(request, body)
    except ValueError as e:
        return _json_error(e)

    denied = _billing_preflight(request, conv, opts)
    if denied:
        return denied

    conv_id = conv.id
    run_id, started = try_start_run(conv_id)
    if not started:
        return JsonResponse(
            {
                "error": "run_in_progress",
                "reply": "یک پاسخ دیگر در حال اجراست — صبر کنید یا آن را متوقف کنید.",
            },
            status=409,
        )
    opts.run_id = run_id

    opts.turn_backup = TurnBackupSession(conv)

    def event_stream():
        try:
            yield _sse({"type": "run_started", "run_id": run_id, "conversation_id": conv_id})
            final: dict | None = None
            try:
                for event in run_agent_events(message, history=history, options=opts):
                    if event.get("type") == "error":
                        with project_backup_lock(conv.project_id):
                            _rollback_turn_session(opts)
                        yield _sse(event)
                        return
                    if event.get("type") == "done":
                        final = event
                    yield _sse(event)
                    yield ": keep-alive\n\n"

                if final and not final.get("error"):
                    bill_err = _billing_settle_before_save(request, conv, final, opts)
                    if bill_err:
                        with project_backup_lock(conv.project_id):
                            _rollback_turn_session(opts)
                        yield _sse(
                            {
                                "type": "error",
                                "error": "insufficient_balance",
                                "reply": "اعتبار کافی نیست",
                            }
                        )
                        return
                    backup = None
                    with project_backup_lock(conv.project_id):
                        try:
                            backup = opts.turn_backup.finalize_record()
                        except (BackupError, OSError) as exc:
                            _rollback_turn_session(opts)
                            yield _sse(
                                {
                                    "type": "error",
                                    "error": "backup_failed",
                                    "reply": f"ذخیرهٔ بک‌آپ تغییرات ناموفق بود: {exc}",
                                }
                            )
                            return
                    save_conv = Conversation.objects.select_related("project").get(
                        pk=conv_id
                    )
                    assistant = save_chat_turn(
                        save_conv,
                        message,
                        final.get("reply", "") or "",
                        final.get("tool_steps") or [],
                        backup=backup,
                        phase_log=final.get("phase_log"),
                        thinking=final.get("thinking"),
                        usage=final.get("usage"),
                    )
                    save_conv.refresh_from_db()
                    user = billing_user(request)
                    if user and final.get("usage"):
                        _link_usage_to_assistant(user, save_conv, assistant)
                    saved = {
                        "type": "saved",
                        "conversation_id": conv_id,
                        "assistant_message_id": assistant.id,
                        "can_undo": backup is not None,
                        "history": save_conv.to_history(),
                    }
                    if billing_user(request):
                        saved["wallet"] = wallet_summary(request.user)
                    if final.get("usage"):
                        saved["usage"] = final.get("usage")
                    yield _sse(saved)
                elif final:
                    with project_backup_lock(conv.project_id):
                        _rollback_turn_session(opts)
                    yield _sse(
                        {
                            "type": "error",
                            "error": final.get("error") or "agent_failed",
                            "reply": final.get("reply")
                            or "اجرای ایجنت بدون ذخیرهٔ موفق تمام شد.",
                        }
                    )
                else:
                    with project_backup_lock(conv.project_id):
                        _rollback_turn_session(opts)
                    yield _sse(
                        {
                            "type": "error",
                            "error": "incomplete_run",
                            "reply": "اجرای ایجنت بدون رویداد پایان قطع شد.",
                        }
                    )
            except Exception:
                with project_backup_lock(conv.project_id):
                    _rollback_turn_session(opts)
                raise
        except Exception as exc:
            yield _sse(
                {
                    "type": "error",
                    "error": "internal",
                    "reply": f"خطا در اجرای ایجنت: {exc}",
                }
            )
        finally:
            from agent.workspace_io import close_remote_session

            close_remote_session(opts)
            end_run(conv_id, run_id)

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@csrf_exempt
@require_user
@require_POST
def chat_cancel(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    cid = body.get("conversation_id")
    run_id = (body.get("run_id") or "").strip()
    if not cid or not run_id:
        return JsonResponse({"error": "conversation_id و run_id الزامی است"}, status=400)
    conv = get_object_or_404(Conversation, pk=int(cid))
    denied = _billing_preflight(request, conv)
    if denied:
        return denied
    if not conversation_owned(request, conv):
        return JsonResponse({"error": "دسترسی مجاز نیست"}, status=403)
    ok = request_cancel(int(cid), run_id)
    return JsonResponse({"ok": ok})


@csrf_exempt
@require_user
@require_POST
def chat_permission(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    request_id = (body.get("request_id") or "").strip()
    if not request_id:
        return JsonResponse({"error": "request_id الزامی است"}, status=400)
    approved = bool(body.get("approved"))
    ok = resolve_permission(request_id, approved)
    if not ok:
        return JsonResponse({"error": "درخواست منقضی یا نامعتبر است"}, status=404)
    return JsonResponse({"ok": True, "approved": approved})


@csrf_exempt
@require_user
@require_POST
def chat_user_input(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    request_id = (body.get("request_id") or "").strip()
    if not request_id:
        return JsonResponse({"error": "request_id الزامی است"}, status=400)
    cancelled = bool(body.get("cancelled"))
    if cancelled:
        ok = resolve_user_input(request_id, {"cancelled": True})
    else:
        values = body.get("values")
        if not isinstance(values, dict):
            return JsonResponse({"error": "values باید شیء باشد"}, status=400)
        notes = str(body.get("notes") or "").strip()
        payload: dict = {"values": values, "cancelled": False}
        if notes:
            payload["notes"] = notes
        ok = resolve_user_input(request_id, payload)
    if not ok:
        return JsonResponse({"error": "درخواست منقضی یا نامعتبر است"}, status=404)
    return JsonResponse({"ok": True})


@require_user
@require_GET
def undo_message_preview(request, message_id: int):
    message = get_object_or_404(
        ChatMessage.objects.select_related("conversation__project", "backup"),
        pk=message_id,
    )
    conv = message.conversation
    if not conversation_owned(request, conv):
        return JsonResponse({"error": "دسترسی مجاز نیست"}, status=403)
    if message.role != ChatMessage.ROLE_ASSISTANT:
        return JsonResponse({"error": "فقط پاسخ ایجنت قابل بازگردانی است"}, status=400)
    try:
        preview = undo_preview_for_message(conv, message)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except BackupError as exc:
        return JsonResponse({"error": str(exc)}, status=500)
    return JsonResponse(preview)


@require_user
@require_GET
def restore_file_preview(request, message_id: int):
    rel_path = (request.GET.get("path") or "").strip()
    if not rel_path:
        return JsonResponse({"error": "مسیر فایل الزامی است"}, status=400)
    message = get_object_or_404(
        ChatMessage.objects.select_related("conversation__project", "backup"),
        pk=message_id,
    )
    conv = message.conversation
    if not conversation_owned(request, conv):
        return JsonResponse({"error": "دسترسی مجاز نیست"}, status=403)
    if message.role != ChatMessage.ROLE_ASSISTANT:
        return JsonResponse({"error": "فقط پاسخ ایجنت قابل بازگردانی است"}, status=400)
    try:
        preview = file_restore_preview_for_message(conv, message, rel_path)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except BackupError as exc:
        return JsonResponse({"error": str(exc)}, status=500)
    return JsonResponse(preview)


@csrf_exempt
@require_user
@require_POST
def restore_turn_file(request, message_id: int):
    confirm = False
    rel_path = ""
    try:
        if request.body:
            body = json.loads(request.body.decode("utf-8"))
            confirm = bool(body.get("confirm"))
            rel_path = (body.get("path") or "").strip()
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    if not rel_path:
        return JsonResponse({"error": "مسیر فایل الزامی است"}, status=400)

    message = get_object_or_404(
        ChatMessage.objects.select_related("conversation__project", "backup"),
        pk=message_id,
    )
    conv = message.conversation
    if not conversation_owned(request, conv):
        return JsonResponse({"error": "دسترسی مجاز نیست"}, status=403)
    if message.role != ChatMessage.ROLE_ASSISTANT:
        return JsonResponse({"error": "فقط پاسخ ایجنت قابل بازگردانی است"}, status=400)
    try:
        preview = file_restore_preview_for_message(conv, message, rel_path)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except BackupError as exc:
        return JsonResponse({"error": str(exc)}, status=500)

    must_confirm = preview.get("legacy_full_backup") or preview.get("needs_confirmation")
    if must_confirm and not confirm:
        return JsonResponse(
            {"error": "confirmation_required", "preview": preview},
            status=409,
        )
    if preview.get("legacy_full_backup"):
        return JsonResponse(
            {"error": "بازگردانی تک‌فایلی برای این نوبت پشتیبانی نمی‌شود"},
            status=400,
        )

    try:
        restore_assistant_turn_file(message_id, rel_path)
    except ChatMessage.DoesNotExist:
        return JsonResponse({"error": "پیام پیدا نشد"}, status=404)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except BackupError as exc:
        return JsonResponse({"error": str(exc)}, status=500)
    return JsonResponse({"ok": True, "path": preview.get("path")})


@csrf_exempt
@require_user
@require_POST
def undo_message(request, message_id: int):
    confirm = False
    try:
        if request.body:
            body = json.loads(request.body.decode("utf-8"))
            confirm = bool(body.get("confirm"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    message = get_object_or_404(
        ChatMessage.objects.select_related("conversation__project", "backup"),
        pk=message_id,
    )
    conv = message.conversation
    if not conversation_owned(request, conv):
        return JsonResponse({"error": "دسترسی مجاز نیست"}, status=403)
    try:
        preview = undo_preview_for_message(conv, message)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except BackupError as exc:
        return JsonResponse({"error": str(exc)}, status=500)

    must_confirm = preview.get("legacy_full_backup") or preview.get("needs_confirmation")
    if must_confirm and not confirm:
        return JsonResponse(
            {
                "error": "confirmation_required",
                "preview": preview,
            },
            status=409,
        )

    try:
        conv = undo_assistant_message(message_id)
    except ChatMessage.DoesNotExist:
        return JsonResponse({"error": "پیام پیدا نشد"}, status=404)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except BackupError as exc:
        return JsonResponse({"error": str(exc)}, status=500)
    return JsonResponse(
        {
            "ok": True,
            "conversation": conversation_to_dict(conv, include_messages=True),
        }
    )
