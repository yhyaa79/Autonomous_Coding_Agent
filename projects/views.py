import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from agent.constants import DEFAULT_AGENT_ID, normalize_agent_id
from agent.registry import ensure_agents_loaded, list_agents, valid_agent_ids
from agent.security import require_api_token

from .auth_api import billing_user, conversation_owned, projects_queryset, require_user
from agent.code_changes import (
    MessageBackupMissing,
    conversation_code_changes,
    turn_code_changes,
)
from agent.message_backup import BackupError

from .models import (
    ChatMessage,
    Conversation,
    Project,
    ProjectServerConnection,
    ScheduledJob,
    SharedTool,
)
from .remote_server import (
    RemoteServerConfig,
    encrypt_secret,
    public_status,
    test_ssh_connection,
    validate_fingerprint,
    remote_root_path_from_request,
    validate_remote_root_path,
)
from agent.model_catalog import models_for_api, resolve_model_id
from .billing import wallet_summary
from .models import UserFileAccess, UserLlmSettings
from .user_file_access import user_file_access_public
from .user_llm import (
    encrypt_api_key,
    user_llm_public_status,
    validate_remote_api_key,
)
from .services import (
    conversation_to_dict,
    project_to_dict,
    validate_project_path,
)
from .shared_tools import (
    attach_by_public_ref,
    create_knowledge_resource,
    delete_resource_family,
    delete_shared_tool,
    detach_shared_tool_from_conversation,
    get_version_by_public_id,
    list_tools_for_conversation_ui,
    list_tools_for_library,
    list_conversation_shared_tools,
    list_versions_for_family,
    parse_public_ref,
    set_conversation_resource_version,
    shared_tool_to_dict,
    update_version_from_payload,
)


def _job_to_dict(j: ScheduledJob, *, detailed: bool = False) -> dict:
    payload = j.payload or {}
    data = {
        "id": j.id,
        "project_id": j.project_id,
        "title": j.title,
        "target_agent_type": j.target_agent_type,
        "created_by_agent_type": j.created_by_agent_type,
        "schedule_kind": j.schedule_kind,
        "run_at": j.run_at.isoformat() if j.run_at else None,
        "cron_expression": j.cron_expression,
        "interval_seconds": j.interval_seconds,
        "timezone_name": j.timezone_name,
        "next_run_at": j.next_run_at.isoformat() if j.next_run_at else None,
        "last_run_at": j.last_run_at.isoformat() if j.last_run_at else None,
        "status": j.status,
        "run_count": j.run_count,
        "max_runs": j.max_runs,
        "last_error": j.last_error,
        "message_preview": (payload.get("message") or "")[:120],
    }
    if detailed:
        data["message"] = payload.get("message") or ""
        data["options"] = payload.get("options") or {}
    return data


@require_GET
def billing_models_api(request):
    return JsonResponse({"models": models_for_api(), "currency_label": "اعتبار ACA"})


@csrf_exempt
@require_user
@require_http_methods(["GET", "POST", "DELETE"])
def user_llm_settings_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "ورود لازم است"}, status=401)
    if request.method == "GET":
        return JsonResponse(user_llm_public_status(request.user))

    if request.method == "DELETE":
        UserLlmSettings.objects.filter(user=request.user).delete()
        return JsonResponse({"ok": True, **user_llm_public_status(request.user)})

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    api_key = (body.get("api_key") or "").strip()
    base_url = (body.get("base_url") or "").strip()
    remote_model = (body.get("remote_model") or "").strip()
    is_enabled = bool(body.get("is_enabled", True))

    row, _ = UserLlmSettings.objects.get_or_create(user=request.user)
    if api_key:
        if not remote_model:
            return JsonResponse({"error": "نام مدل (remote_model) الزامی است"}, status=400)
        try:
            validate_remote_api_key(api_key, base_url, remote_model)
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        row.api_key_encrypted = encrypt_api_key(api_key)
        row.remote_model = remote_model
        if base_url:
            row.base_url = base_url
    elif not row.api_key_encrypted:
        return JsonResponse({"error": "کلید API الزامی است"}, status=400)

    if remote_model and not api_key:
        row.remote_model = remote_model
    if "base_url" in body:
        row.base_url = base_url
    row.is_enabled = is_enabled
    row.save()
    return JsonResponse({"ok": True, **user_llm_public_status(request.user)})


@csrf_exempt
@require_user
@require_http_methods(["GET", "PATCH"])
def user_file_access_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "ورود لازم است"}, status=401)
    if request.method == "GET":
        return JsonResponse(user_file_access_public(request.user))

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    from agent.scope import normalize_scope_paths

    row, _ = UserFileAccess.objects.get_or_create(user=request.user)
    update_fields: list[str] = []
    if "always_context_paths" in body:
        if not isinstance(body["always_context_paths"], list):
            return JsonResponse({"error": "always_context_paths باید آرایه باشد"}, status=400)
        row.always_context_paths = normalize_scope_paths(body["always_context_paths"])
        update_fields.append("always_context_paths")
    if "denied_content_paths" in body:
        if not isinstance(body["denied_content_paths"], list):
            return JsonResponse({"error": "denied_content_paths باید آرایه باشد"}, status=400)
        row.denied_content_paths = normalize_scope_paths(body["denied_content_paths"])
        update_fields.append("denied_content_paths")
    if not update_fields:
        return JsonResponse({"error": "فیلدی برای به‌روزرسانی نیست"}, status=400)
    row.save(update_fields=[*update_fields, "updated_at"])
    return JsonResponse({"ok": True, **user_file_access_public(request.user)})


@require_user
@require_GET
def billing_wallet_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "ورود لازم است"}, status=401)
    return JsonResponse(wallet_summary(request.user))


@require_GET
def agent_types(request):
    ensure_agents_loaded()
    return JsonResponse({"agents": list_agents()})


@require_user
@require_GET
def project_list(request):
    items = [project_to_dict(p) for p in projects_queryset(request)]
    return JsonResponse({"projects": items})


@require_user
@require_GET
def project_browse_dirs(request):
    """List subdirectories on the server for the new-project folder picker."""
    from pathlib import Path

    import os

    raw = (request.GET.get("path") or "").strip()
    if not raw:
        raw = str(Path.home())
    try:
        current = Path(raw).expanduser().resolve()
    except (OSError, ValueError) as e:
        return JsonResponse({"error": str(e)}, status=400)
    if not current.is_dir():
        return JsonResponse({"error": "مسیر پوشه نیست"}, status=400)

    parent = None
    if current.parent != current:
        parent = str(current.parent)

    entries: list[dict] = []
    try:
        names = sorted(os.listdir(current), key=str.lower)
    except OSError as e:
        return JsonResponse({"error": str(e)}, status=403)

    for name in names:
        if name.startswith("."):
            continue
        full = current / name
        try:
            if full.is_dir():
                entries.append({"name": name, "path": str(full), "type": "dir"})
        except OSError:
            continue

    return JsonResponse({"path": str(current), "parent": parent, "entries": entries})


@csrf_exempt
@require_user
@require_http_methods(["POST"])
def project_create(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = (body.get("name") or "").strip()
    root_path = (body.get("root_path") or "").strip()
    remote_body = body.get("remote") if isinstance(body.get("remote"), dict) else {}
    remote_enabled = bool(remote_body.get("enabled"))
    if not name:
        return JsonResponse({"error": "name الزامی است"}, status=400)
    if remote_enabled:
        remote_root_raw = (remote_body.get("remote_root_path") or "").strip()
        if not remote_root_raw:
            return JsonResponse(
                {"error": "برای پروژهٔ راه‌دور، مسیر پروژه روی سرور الزامی است"},
                status=400,
            )
        try:
            validated_remote = validate_remote_root_path(remote_root_raw)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        validated = validated_remote
    else:
        if not root_path:
            return JsonResponse({"error": "name و root_path الزامی است"}, status=400)
        try:
            validated = str(validate_project_path(root_path))
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

    default_scope = body.get("default_scope_paths") or []
    if not isinstance(default_scope, list):
        default_scope = []

    project = Project.objects.create(
        name=name,
        root_path=str(validated),
        default_scope_paths=default_scope,
        owner=billing_user(request),
    )
    if remote_enabled:
        err = _save_project_remote_connection(project, remote_body, require_secret=True)
        if err:
            project.delete()
            return JsonResponse({"error": err}, status=400)
    else:
        from agent.project_data import prepare_project_store

        prepare_project_store(project)
    return JsonResponse({"project": project_to_dict(project)}, status=201)


def _remote_config_from_body(body: dict, row: ProjectServerConnection | None) -> RemoteServerConfig | None:
    host = (body.get("host") or "").strip()
    username = (body.get("username") or "").strip()
    raw_root = remote_root_path_from_request(body, row)
    if not raw_root:
        return None
    try:
        remote_root = validate_remote_root_path(raw_root)
    except ValueError:
        return None
    port = int(body.get("port") or (row.port if row else 22) or 22)
    auth_method = (body.get("auth_method") or (row.auth_method if row else "password")).strip()
    secret = (body.get("password") or body.get("private_key") or "").strip()
    if not secret and row and row.secret_encrypted:
        from .remote_server import decrypt_secret

        try:
            secret = decrypt_secret(row.secret_encrypted)
        except Exception:
            secret = ""
    if not host or not username or not secret:
        return None
    passphrase = (body.get("key_passphrase") or "").strip()
    if not passphrase and row and row.key_passphrase_encrypted:
        from .remote_server import decrypt_secret

        try:
            passphrase = decrypt_secret(row.key_passphrase_encrypted)
        except Exception:
            passphrase = ""
    strict = bool(body.get("strict_host_key", row.strict_host_key if row else True))
    try:
        fp = validate_fingerprint(body.get("host_key_fingerprint") or (row.host_key_fingerprint if row else ""))
    except ValueError:
        return None
    return RemoteServerConfig(
        host=host,
        port=port,
        username=username,
        auth_method=auth_method,
        secret=secret,
        passphrase=passphrase,
        remote_root_path=remote_root,
        strict_host_key=strict,
        host_key_fingerprint=fp,
        allow_server_wide_paths=bool(
            body.get(
                "allow_server_wide_paths",
                row.allow_server_wide_paths if row else False,
            )
        ),
    )


def _save_project_remote_connection(
    project: Project,
    body: dict,
    *,
    require_secret: bool,
) -> str | None:
    row, _ = ProjectServerConnection.objects.get_or_create(project=project)
    host = (body.get("host") or "").strip()
    username = (body.get("username") or "").strip()
    raw_root = remote_root_path_from_request(body, row)
    if raw_root:
        try:
            remote_root = validate_remote_root_path(raw_root)
        except ValueError as exc:
            return str(exc)
    elif "remote_root_path" in body:
        remote_root = ""
    else:
        remote_root = (row.remote_root_path or "").strip()
    port = int(body.get("port") or row.port or 22)
    if port < 1 or port > 65535:
        return "پورت نامعتبر است"
    auth_method = (body.get("auth_method") or "password").strip()
    if auth_method not in (
        ProjectServerConnection.AUTH_PASSWORD,
        ProjectServerConnection.AUTH_PRIVATE_KEY,
    ):
        return "روش احراز هویت نامعتبر است"
    secret_plain = (body.get("password") or body.get("private_key") or "").strip()
    if secret_plain:
        try:
            row.secret_encrypted = encrypt_secret(secret_plain)
        except ValueError as exc:
            return str(exc)
    elif require_secret and not row.secret_encrypted:
        return "رمز عبور یا کلید خصوصی الزامی است"
    passphrase = (body.get("key_passphrase") or "").strip()
    if passphrase:
        row.key_passphrase_encrypted = encrypt_secret(passphrase)
    elif "key_passphrase" in body and not passphrase:
        row.key_passphrase_encrypted = ""
    try:
        row.host_key_fingerprint = validate_fingerprint(body.get("host_key_fingerprint") or "")
    except ValueError as exc:
        return str(exc)
    row.host = host
    row.port = port
    row.username = username
    row.auth_method = auth_method
    row.remote_root_path = remote_root
    row.strict_host_key = bool(body.get("strict_host_key", True))
    row.is_enabled = bool(body.get("is_enabled", body.get("enabled", False)))
    row.allow_server_wide_paths = bool(body.get("allow_server_wide_paths", False))
    if row.is_enabled:
        if not host or not username:
            return "برای فعال‌سازی SSH، host و username الزامی است"
        if not remote_root:
            return "مسیر پروژه روی سرور الزامی است (مسیر لینوکس روی VPS، نه مسیر مک/ویندوز لوکال)"
    row.save()
    return None


@csrf_exempt
@require_user
@require_http_methods(["GET", "POST", "DELETE"])
def project_remote_server_api(request, project_id: int):
    project = get_object_or_404(projects_queryset(request), pk=project_id)
    if request.method == "GET":
        return JsonResponse(public_status(project))

    if request.method == "DELETE":
        ProjectServerConnection.objects.filter(project=project).delete()
        return JsonResponse({"ok": True, **public_status(project)})

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    err = _save_project_remote_connection(project, body, require_secret=False)
    if err:
        return JsonResponse({"error": err}, status=400)
    return JsonResponse({"ok": True, **public_status(project)})


@csrf_exempt
@require_user
@require_http_methods(["POST"])
def project_remote_server_test_api(request, project_id: int):
    project = get_object_or_404(projects_queryset(request), pk=project_id)
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        body = {}
    row = None
    try:
        row = project.server_connection
    except ProjectServerConnection.DoesNotExist:
        row = None
    cfg = _remote_config_from_body(body, row)
    if not cfg:
        raw_root = remote_root_path_from_request(body, row)
        if "remote_root_path" in body and not raw_root:
            return JsonResponse(
                {
                    "ok": False,
                    "error": "مسیر پروژه روی سرور الزامی است (مثلاً /root/startup_design_django)",
                },
                status=400,
            )
        return JsonResponse({"error": "تنظیمات SSH ناقص است"}, status=400)
    try:
        result = test_ssh_connection(cfg)
    except Exception as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
    return JsonResponse({"ok": True, **result})


@csrf_exempt
@require_user
@require_http_methods(["GET", "PATCH"])
def project_growth_hub_api(request, project_id: int):
    from projects.growth_hub import apply_hub_patch, get_or_create_hub, hub_public_dict

    project = get_object_or_404(projects_queryset(request), pk=project_id)
    hub = get_or_create_hub(project)
    if request.method == "GET":
        return JsonResponse({"growth_hub": hub_public_dict(hub)})
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    ok, msg = apply_hub_patch(hub, body)
    if not ok:
        return JsonResponse({"error": msg}, status=400)
    hub.refresh_from_db()
    return JsonResponse({"ok": True, "message": msg, "growth_hub": hub_public_dict(hub)})


@csrf_exempt
@require_user
def project_debug_hub_api(request, project_id: int):
    from projects.debug_hub import (
        apply_profile_patch,
        get_or_create_profile,
        hub_public_dict,
        scan_to_dict,
    )
    from projects.models import DebugScan

    project = get_object_or_404(projects_queryset(request), pk=project_id)
    if request.method == "GET":
        return JsonResponse({"debug_hub": hub_public_dict(project)})
    if request.method != "PATCH":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    profile = get_or_create_profile(project)
    ok, msg = apply_profile_patch(profile, body)
    if not ok:
        return JsonResponse({"error": msg}, status=400)
    scan_id = body.get("load_scan_id")
    if scan_id is not None:
        scan = get_object_or_404(DebugScan, pk=int(scan_id), project=project)
        return JsonResponse(
            {
                "ok": True,
                "message": msg,
                "debug_hub": hub_public_dict(project),
                "scan": scan_to_dict(scan),
            }
        )
    return JsonResponse({"ok": True, "message": msg, "debug_hub": hub_public_dict(project)})


@csrf_exempt
@require_user
@require_http_methods(["POST"])
def project_debug_scan_api(request, project_id: int):
    from projects.debug_hub import execute_scan, hub_public_dict, scan_to_dict

    project = get_object_or_404(projects_queryset(request), pk=project_id)
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    url = str(body.get("url") or "").strip()
    categories = body.get("categories")
    if categories is not None and not isinstance(categories, list):
        return JsonResponse({"error": "categories باید آرایه باشد"}, status=400)
    try:
        scan = execute_scan(project, url, categories)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse(
        {
            "ok": True,
            "scan": scan_to_dict(scan),
            "debug_hub": hub_public_dict(project),
        },
        status=201,
    )


@csrf_exempt
@require_user
@require_http_methods(["DELETE"])
def project_delete(request, project_id: int):
    project = get_object_or_404(projects_queryset(request), pk=project_id)
    project.delete()
    return JsonResponse({"ok": True})


@csrf_exempt
@require_user
@require_http_methods(["PATCH"])
def project_update(request, project_id: int):
    project = get_object_or_404(projects_queryset(request), pk=project_id)
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    from agent.scope import normalize_scope_paths

    update_fields: list[str] = []
    if "always_context_paths" in body:
        if not isinstance(body["always_context_paths"], list):
            return JsonResponse({"error": "always_context_paths باید آرایه باشد"}, status=400)
        project.always_context_paths = normalize_scope_paths(body["always_context_paths"])
        update_fields.append("always_context_paths")
    if "denied_content_paths" in body:
        if not isinstance(body["denied_content_paths"], list):
            return JsonResponse({"error": "denied_content_paths باید آرایه باشد"}, status=400)
        project.denied_content_paths = normalize_scope_paths(body["denied_content_paths"])
        update_fields.append("denied_content_paths")
    if "default_scope_paths" in body and isinstance(body["default_scope_paths"], list):
        project.default_scope_paths = normalize_scope_paths(body["default_scope_paths"])
        update_fields.append("default_scope_paths")

    if not update_fields:
        return JsonResponse({"error": "فیلدی برای به‌روزرسانی نیست"}, status=400)
    project.updated_at = timezone.now()
    update_fields.append("updated_at")
    project.save(update_fields=update_fields)
    return JsonResponse({"project": project_to_dict(project)})


@require_user
@require_GET
def conversation_list(request, project_id: int):
    project = get_object_or_404(projects_queryset(request), pk=project_id)
    items = [conversation_to_dict(c) for c in project.conversations.all()]
    return JsonResponse({"conversations": items, "project": project_to_dict(project)})


@csrf_exempt
@require_user
@require_http_methods(["POST"])
def conversation_create(request, project_id: int):
    project = get_object_or_404(projects_queryset(request), pk=project_id)
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        body = {}

    title = (body.get("title") or "مکالمه جدید").strip()
    scope_paths = body.get("scope_paths")
    if scope_paths is None:
        scope_paths = list(project.default_scope_paths or [])
    elif not isinstance(scope_paths, list):
        scope_paths = []

    ensure_agents_loaded()
    raw = str(body.get("agent_type") or DEFAULT_AGENT_ID).strip()
    if raw not in valid_agent_ids():
        agent_type = DEFAULT_AGENT_ID
    else:
        agent_type = normalize_agent_id(raw)

    conv = Conversation.objects.create(
        project=project,
        agent_type=agent_type,
        title=title,
        scope_paths=scope_paths,
        scope_note=str(body.get("scope_note") or ""),
        llm_model=resolve_model_id(str(body.get("llm_model") or "")),
    )
    return JsonResponse({"conversation": conversation_to_dict(conv)}, status=201)


@require_user
@require_GET
def conversation_detail(request, conversation_id: int):
    conv = get_object_or_404(Conversation, pk=conversation_id)
    if not conversation_owned(request, conv):
        return JsonResponse({"error": "دسترسی مجاز نیست"}, status=403)
    return JsonResponse(
        {"conversation": conversation_to_dict(conv, include_messages=True)}
    )


@csrf_exempt
@require_user
@require_http_methods(["PATCH", "PUT"])
def conversation_update(request, conversation_id: int):
    conv = get_object_or_404(Conversation, pk=conversation_id)
    if not conversation_owned(request, conv):
        return JsonResponse({"error": "دسترسی مجاز نیست"}, status=403)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if "title" in body:
        conv.title = str(body["title"]).strip()[:300] or conv.title
    if "scope_paths" in body and isinstance(body["scope_paths"], list):
        conv.scope_paths = body["scope_paths"]
    if "scope_note" in body:
        conv.scope_note = str(body["scope_note"])
    if "agent_type" in body:
        ensure_agents_loaded()
        at = str(body["agent_type"]).strip()
        if at in valid_agent_ids():
            conv.agent_type = normalize_agent_id(at)
    if "llm_model" in body:
        conv.llm_model = resolve_model_id(str(body.get("llm_model") or ""))
    conv.save()
    return JsonResponse({"conversation": conversation_to_dict(conv)})


@csrf_exempt
@require_http_methods(["DELETE"])
def conversation_delete(request, conversation_id: int):
    conv = get_object_or_404(Conversation, pk=conversation_id)
    conv.delete()
    return JsonResponse({"ok": True})


@require_GET
def scheduled_job_list(request, project_id: int):
    from agent.scheduler_service import repair_job_schedules

    project = get_object_or_404(Project, pk=project_id)
    repair_job_schedules(project_id=project_id)
    jobs = [_job_to_dict(j) for j in project.scheduled_jobs.all()[:50]]
    return JsonResponse({"jobs": jobs})


@csrf_exempt
@require_http_methods(["POST"])
def scheduled_project_tick(request, project_id: int):
    from agent.scheduler_service import tick_due_jobs

    get_object_or_404(Project, pk=project_id)
    results = tick_due_jobs(limit=5, project_id=project_id)
    return JsonResponse({"ok": True, "results": results})


@require_GET
def project_job_runs(request, project_id: int):
    from projects.models import JobRun

    get_object_or_404(Project, pk=project_id)
    runs = (
        JobRun.objects.filter(job__project_id=project_id)
        .select_related("job")
        .order_by("-started_at")[:40]
    )
    items = [
        {
            "id": r.id,
            "job_id": r.job_id,
            "job_title": r.job.title,
            "status": r.status,
            "error_code": r.error_code,
            "started_at": r.started_at.isoformat(),
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "reply": r.reply or "",
            "tool_steps": r.tool_steps or [],
        }
        for r in runs
    ]
    return JsonResponse({"runs": items})


@csrf_exempt
@require_http_methods(["POST"])
def scheduled_job_create(request, project_id: int):
    from agent.scheduler_service import _parse_run_at, refresh_next_run

    project = get_object_or_404(Project, pk=project_id)
    tz_default = "Asia/Tehran"
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    title = (body.get("title") or "Job").strip()[:200]
    message = (body.get("message") or "").strip()
    if not message:
        return JsonResponse({"error": "message الزامی است"}, status=400)

    job = ScheduledJob(
        project=project,
        title=title,
        target_agent_type=normalize_agent_id(
            str(body.get("target_agent_type") or DEFAULT_AGENT_ID)
        ),
        created_by_agent_type=str(body.get("created_by_agent_type") or "user"),
        payload={"message": message, "options": body.get("options") or {}},
        schedule_kind=str(body.get("schedule_kind") or ScheduledJob.KIND_ONCE),
        run_at=_parse_run_at(
            body.get("run_at"),
            str(body.get("timezone") or body.get("timezone_name") or tz_default),
        )
        if body.get("run_at")
        else None,
        cron_expression=str(body.get("cron_expression") or ""),
        interval_seconds=body.get("interval_seconds"),
        timezone_name=str(body.get("timezone") or body.get("timezone_name") or tz_default),
        max_runs=body.get("max_runs"),
    )
    try:
        job.full_clean()
        job.save()
        refresh_next_run(job)
        job.save()
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"job": _job_to_dict(job)}, status=201)


@require_GET
def scheduled_job_detail(request, job_id: int):
    job = get_object_or_404(ScheduledJob, pk=job_id)
    return JsonResponse({"job": _job_to_dict(job, detailed=True)})


@csrf_exempt
@require_http_methods(["PATCH", "PUT"])
def scheduled_job_update(request, job_id: int):
    from agent.scheduler_service import _parse_run_at, refresh_next_run

    job = get_object_or_404(ScheduledJob, pk=job_id)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if "title" in body:
        job.title = str(body["title"]).strip()[:200] or job.title
    if "target_agent_type" in body:
        job.target_agent_type = normalize_agent_id(
            str(body["target_agent_type"]).strip() or DEFAULT_AGENT_ID
        )
    if "message" in body:
        payload = dict(job.payload or {})
        payload["message"] = str(body["message"]).strip()
        job.payload = payload
    if "schedule_kind" in body:
        kind = str(body["schedule_kind"]).strip()
        if kind in {c[0] for c in ScheduledJob.KIND_CHOICES}:
            job.schedule_kind = kind
    if "run_at" in body:
        raw = body["run_at"]
        tz = str(
            body.get("timezone")
            or body.get("timezone_name")
            or job.timezone_name
            or "Asia/Tehran"
        )
        job.run_at = _parse_run_at(raw, tz) if raw else None
    if "cron_expression" in body:
        job.cron_expression = str(body["cron_expression"] or "")
    if "interval_seconds" in body:
        val = body["interval_seconds"]
        job.interval_seconds = int(val) if val is not None else None
    if "timezone" in body or "timezone_name" in body:
        job.timezone_name = str(
            body.get("timezone") or body.get("timezone_name") or job.timezone_name
        )
    if "max_runs" in body:
        val = body["max_runs"]
        job.max_runs = int(val) if val is not None else None
    if "status" in body and body["status"] in {
        s[0] for s in ScheduledJob.STATUS_CHOICES
    }:
        job.status = body["status"]

    try:
        job.full_clean()
        if job.status == ScheduledJob.STATUS_ACTIVE:
            refresh_next_run(job)
        job.save()
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"job": _job_to_dict(job, detailed=True)})


@csrf_exempt
@require_http_methods(["DELETE"])
def scheduled_job_delete(request, job_id: int):
    job = get_object_or_404(ScheduledJob, pk=job_id)
    job.delete()
    return JsonResponse({"ok": True})


@csrf_exempt
@require_http_methods(["GET", "DELETE", "PATCH"])
def shared_tool_detail(request, public_id: str):
    ref = parse_public_ref(public_id) or public_id.strip().lower()
    version = get_version_by_public_id(ref)
    if request.method == "DELETE":
        if version:
            if not delete_shared_tool(ref):
                return JsonResponse({"error": "منبع پیدا نشد"}, status=404)
            return JsonResponse({"ok": True})
        if delete_resource_family(ref):
            return JsonResponse({"ok": True})
        return JsonResponse({"error": "منبع پیدا نشد"}, status=404)
    if request.method == "PATCH":
        if not version:
            return JsonResponse({"error": "ورژن پیدا نشد"}, status=404)
        try:
            body = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        if body.get("create_new_version"):
            new_v = update_version_from_payload(version, body)
            return JsonResponse(
                {
                    "tool": shared_tool_to_dict(
                        new_v.shared_tool,
                        request=request,
                        version=new_v,
                        include_source=True,
                    ),
                    "versions": list_versions_for_family(new_v.shared_tool),
                }
            )
        return JsonResponse({"error": "فقط create_new_version پشتیبانی می‌شود"}, status=400)
    if not version:
        return JsonResponse({"error": "منبع پیدا نشد"}, status=404)
    family = version.shared_tool
    include = request.GET.get("full") == "1" or request.GET.get("include_source") == "1"
    return JsonResponse(
        {
            "tool": shared_tool_to_dict(
                family,
                request=request,
                version=version,
                include_source=include,
            ),
            "versions": list_versions_for_family(family),
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def shared_tool_create(request):
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    from agent.project_tools.validator import ToolValidationError

    try:
        version = create_knowledge_resource(
            tool_id=str(body.get("tool_id") or ""),
            display_name=str(body.get("display_name") or body.get("tool_id") or ""),
            description=str(body.get("description") or ""),
            content_kind=str(body.get("content_kind") or "prompt"),
            content_blocks=body.get("content_blocks"),
            source_body=str(body.get("source_body") or ""),
            parameters=body.get("parameters") if isinstance(body.get("parameters"), dict) else {},
            source_project_id=None,
            tags=body.get("tags"),
        )
    except ToolValidationError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    family = version.shared_tool
    return JsonResponse(
        {
            "tool": shared_tool_to_dict(
                family, request=request, version=version, include_source=True
            ),
            "versions": list_versions_for_family(family),
        },
        status=201,
    )


@require_GET
def shared_tool_library(request):
    limit = request.GET.get("limit", "300")
    try:
        cap = int(limit)
    except (TypeError, ValueError):
        cap = 300
    tools, total = list_tools_for_library(request=request, limit=cap)
    from projects.resource_tags import RESOURCE_TAG_CATALOG

    tag_catalog = {
        k: {"id": k, "label": v[0], "hint": v[1]} for k, v in RESOURCE_TAG_CATALOG.items()
    }
    return JsonResponse(
        {
            "tools": tools,
            "total": total,
            "tag_catalog": tag_catalog,
        }
    )


@require_GET
def conversation_tools_list(request, conversation_id: int):
    conv = get_object_or_404(Conversation, pk=conversation_id)
    return JsonResponse(
        {
            "conversation_id": conv.id,
            "tools": list_tools_for_conversation_ui(conv, request=request),
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def conversation_tool_attach(request, conversation_id: int):
    conv = get_object_or_404(Conversation, pk=conversation_id)
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    raw = (body.get("ref") or body.get("link") or body.get("public_id") or "").strip()
    if not raw:
        return JsonResponse({"error": "ref یا link الزامی است"}, status=400)
    try:
        shared = attach_by_public_ref(conv, raw)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    family = shared.shared_tool
    return JsonResponse(
        {
            "tool": shared_tool_to_dict(family, request=request, version=shared),
            "tools": [
                shared_tool_to_dict(f, request=request, link=link)
                for f, link in list_conversation_shared_tools(conv)
            ],
        },
        status=201,
    )


@csrf_exempt
@require_http_methods(["DELETE"])
def conversation_tool_detach(request, conversation_id: int, public_id: str):
    conv = get_object_or_404(Conversation, pk=conversation_id)
    if not detach_shared_tool_from_conversation(conv, public_id):
        return JsonResponse({"error": "ابزار به این مکالمه وصل نیست"}, status=404)
    return JsonResponse(
        {
            "ok": True,
            "tools": [
                shared_tool_to_dict(f, request=request, link=link)
                for f, link in list_conversation_shared_tools(conv)
            ],
        }
    )


@csrf_exempt
@require_http_methods(["PATCH"])
def conversation_tool_pin_version(request, conversation_id: int, tool_id: str):
    conv = get_object_or_404(Conversation, pk=conversation_id)
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    public_id = body.get("public_id") or body.get("version_public_id")
    try:
        link = set_conversation_resource_version(
            conv,
            tool_id,
            version_public_id=str(public_id).strip() if public_id else None,
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(
        {
            "tool": shared_tool_to_dict(
                link.shared_tool,
                request=request,
                link=link,
            ),
            "tools": [
                shared_tool_to_dict(f, request=request, link=lnk)
                for f, lnk in list_conversation_shared_tools(conv)
            ],
        }
    )


@require_GET
def scheduled_job_runs(request, job_id: int):
    job = get_object_or_404(ScheduledJob, pk=job_id)
    runs = [
        {
            "id": r.id,
            "status": r.status,
            "error_code": r.error_code,
            "started_at": r.started_at.isoformat(),
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "reply_preview": (r.reply or "")[:500],
        }
        for r in job.runs.all()[:20]
    ]
    return JsonResponse({"runs": runs})


@require_user
@require_GET
def conversation_code_changes_api(request, conversation_id: int):
    conv = get_object_or_404(Conversation, pk=conversation_id)
    if not conversation_owned(request, conv):
        return JsonResponse({"error": "دسترسی مجاز نیست"}, status=403)
    try:
        payload = conversation_code_changes(conv)
    except BackupError as exc:
        return JsonResponse({"error": str(exc)}, status=500)
    return JsonResponse(payload)


@require_user
@require_GET
def message_code_changes_api(request, message_id: int):
    message = get_object_or_404(
        ChatMessage.objects.select_related("conversation__project", "backup"),
        pk=message_id,
    )
    conv = message.conversation
    if not conversation_owned(request, conv):
        return JsonResponse({"error": "دسترسی مجاز نیست"}, status=403)
    if message.role != ChatMessage.ROLE_ASSISTANT:
        return JsonResponse({"error": "تغییرات فقط برای پاسخ ایجنت قابل نمایش است"}, status=400)
    try:
        payload = turn_code_changes(conv, message)
    except MessageBackupMissing:
        return JsonResponse({"error": "بک‌آپی برای این پیام وجود ندارد"}, status=404)
    except BackupError as exc:
        return JsonResponse({"error": str(exc)}, status=500)
    return JsonResponse(payload)
