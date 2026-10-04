from pathlib import Path

from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils import timezone

from agent.code_changes import assistant_has_code_changes
from agent.code_changes import assistant_messages_with_backup
from agent.message_backup import (
    BackupError,
    apply_file_states_on_project,
    apply_undo_partial,
    backup_before_state_for_path,
    backup_is_partial_token,
    project_backup_lock,
    restore_project,
    restore_remote_project,
)
from projects.remote_server import project_uses_remote
from agent.options import AgentOptions
from agent.scope import normalize_scope_paths
from agent.security import project_path_allowed

from agent.constants import normalize_agent_id
from agent.history import estimate_history_tokens
from agent.model_catalog import model_context_window, resolve_model_id

from .conversation_feed import (
    add_conversation_credits,
    append_tool_trace,
    build_conversation_timeline,
    make_topic_summary,
    persist_turn_feed,
    rebuild_conversation_ui_state,
)
from .models import ChatMessage, Conversation, MessageBackup, Project


def validate_project_path(root_path: str) -> Path:
    p = Path(root_path).expanduser().resolve()
    if not p.exists():
        raise ValueError("مسیر وجود ندارد")
    if not p.is_dir():
        raise ValueError("مسیر باید یک پوشه باشد")
    if not project_path_allowed(str(p)):
        raise ValueError("مسیر پروژه در allowlist سرور مجاز نیست (AGENT_PROJECT_PATH_ALLOWLIST)")
    return p


def agent_options_for_conversation(
    conv: Conversation,
    extra: dict | None = None,
    user=None,
) -> AgentOptions:
    from agent.registry import ensure_agents_loaded, get_agent

    payload = extra or {}
    base = AgentOptions.from_dict(payload)
    if "scope_paths" in payload and isinstance(payload["scope_paths"], list):
        scopes = normalize_scope_paths(payload["scope_paths"])
    else:
        scopes = conv.user_configured_scope()
    scope_note = ""
    if "scope_note" in payload:
        scope_note = str(payload.get("scope_note") or "")
    ensure_agents_loaded()
    spec = get_agent(conv.agent_type)
    allow_shell = bool(
        payload["allow_shell"] if "allow_shell" in payload else spec.default_allow_shell
    )
    allow_write = bool(
        payload["allow_write"] if "allow_write" in payload else spec.default_allow_write
    )

    model_id = resolve_model_id(base.model or conv.llm_model or None)

    project = conv.project
    from agent.workspace_io import attach_remote_session
    from projects.remote_server import project_remote_config
    from projects.user_file_access import user_file_access_lists

    always_ctx, denied_ctx = user_file_access_lists(user)
    remote_cfg = project_remote_config(project)
    workspace_root = (
        remote_cfg.remote_root_path if remote_cfg else project.root_path
    )
    opts = AgentOptions(
        allow_shell=allow_shell,
        allow_write=allow_write,
        max_tool_rounds=base.max_tool_rounds,
        model=model_id,
        workspace_root=workspace_root,
        scope_paths=scopes,
        scope_note=scope_note,
        always_context_paths=always_ctx,
        denied_content_paths=denied_ctx,
        agent_type=normalize_agent_id(conv.agent_type),
        project_id=conv.project_id,
        conversation_id=conv.id,
        enable_thinking=base.enable_thinking,
        thinking_depth=base.thinking_depth,
    )
    attach_remote_session(opts, remote_cfg)
    return opts


def save_chat_turn(
    conv: Conversation,
    user_message: str,
    assistant_reply: str,
    tool_steps: list,
    backup: MessageBackup | None = None,
    *,
    phase_log: list | None = None,
    thinking: str | None = None,
    usage: dict | None = None,
) -> ChatMessage:
    turn_index = conv.messages.filter(role=ChatMessage.ROLE_USER).count()
    with transaction.atomic():
        ChatMessage.objects.create(
            conversation=conv, role=ChatMessage.ROLE_USER, content=user_message
        )
        persist_turn_feed(
            conv,
            turn_index=turn_index,
            phase_log=phase_log,
            tool_steps=tool_steps,
            thinking=thinking,
            usage=usage,
        )
        assistant = ChatMessage.objects.create(
            conversation=conv,
            role=ChatMessage.ROLE_ASSISTANT,
            content=assistant_reply,
            tool_steps=tool_steps or [],
        )
        if backup is not None:
            backup.message = assistant
            backup.conversation = conv
            backup.project = conv.project
            backup.save(update_fields=["message", "conversation", "project"])
        if conv.title == "مکالمه جدید" and user_message:
            conv.title = user_message.strip()[:80]
        if not conv.topic_summary and user_message:
            conv.topic_summary = make_topic_summary(user_message)
        conv.updated_at = timezone.now()
        conv.save(update_fields=["title", "topic_summary", "updated_at"])
        conv.project.save(update_fields=["updated_at"])
    append_tool_trace(conv, thinking=thinking, tool_steps=tool_steps)
    add_conversation_credits(conv, usage)
    return assistant


def restore_assistant_turn_file(message_id: int, rel_path: str) -> None:
    """فقط یک فایل را به وضعیت قبل از آن نوبت برمی‌گرداند؛ پیام‌ها حذف نمی‌شوند."""
    message = ChatMessage.objects.select_related("conversation__project").get(pk=message_id)
    if message.role != ChatMessage.ROLE_ASSISTANT:
        raise ValueError("فقط پاسخ ایجنت قابل بازگردانی است")
    try:
        backup = message.backup
    except MessageBackup.DoesNotExist:
        raise ValueError("برای این پیام بک‌آپی وجود ندارد") from None

    rel_path = rel_path.replace("\\", "/").strip().lstrip("/")
    if not rel_path:
        raise ValueError("مسیر فایل نامعتبر است")

    project = message.conversation.project
    project_root = Path(project.root_path)
    if not project_uses_remote(project) and not project_root.is_dir():
        raise ValueError("پوشه پروژه پیدا نشد")
    if not backup_is_partial_token(backup.token, project_root):
        raise ValueError("بازگردانی تک‌فایلی برای این نوبت پشتیبانی نمی‌شود")

    with project_backup_lock(project.id):
        target = backup_before_state_for_path(backup.token, project_root, rel_path)
        apply_file_states_on_project(project, {rel_path: target})


def undo_assistant_message(message_id: int) -> Conversation:
    """کل پروژه را به قبل از این پاسخ برمی‌گرداند و این نوبت و پیام‌های بعدش را حذف می‌کند."""
    message = ChatMessage.objects.select_related("conversation__project").get(pk=message_id)
    if message.role != ChatMessage.ROLE_ASSISTANT:
        raise ValueError("فقط پاسخ ایجنت قابل بازگردانی است")
    try:
        backup = message.backup
    except MessageBackup.DoesNotExist:
        raise ValueError("برای این پیام بک‌آپی وجود ندارد") from None

    conv = message.conversation
    project = conv.project
    project_root = Path(project.root_path)
    if not project_uses_remote(project) and not project_root.is_dir():
        raise ValueError("پوشه پروژه پیدا نشد")

    assistants = assistant_messages_with_backup(conv)
    undo_index = next((i for i, m in enumerate(assistants) if m.id == message.id), -1)

    with project_backup_lock(conv.project_id):
        try:
            if backup_is_partial_token(backup.token, project_root):
                if undo_index < 0:
                    raise ValueError("پیام در این مکالمه پیدا نشد")
                apply_undo_partial(project, assistants, undo_index)
            elif project_uses_remote(project):
                restore_remote_project(project, backup.token)
            else:
                restore_project(project_root, backup.token)
        except BackupError:
            raise
        except OSError as exc:
            raise BackupError(f"بازگردانی پروژه ناموفق بود: {exc}") from exc

        messages = list(conv.messages.order_by("created_at", "id"))
        index = next((i for i, item in enumerate(messages) if item.id == message.id), None)
        if index is None:
            raise ValueError("پیام در این مکالمه پیدا نشد")
        start = index
        if start > 0 and messages[start - 1].role == ChatMessage.ROLE_USER:
            start -= 1
        removed_user = messages[start] if messages[start].role == ChatMessage.ROLE_USER else None
        purge_turn = sum(
            1
            for item in messages[:start]
            if item.role == ChatMessage.ROLE_USER
        )
        delete_ids = [item.id for item in messages[start:]]
        with transaction.atomic():
            conv.feed_items.filter(turn_index__gte=purge_turn).delete()
            ChatMessage.objects.filter(pk__in=delete_ids).delete()
            conv.refresh_from_db()
            rebuild_conversation_ui_state(conv)
            if removed_user is not None and conv.title == removed_user.content.strip()[:80]:
                first_user = (
                    conv.messages.filter(role=ChatMessage.ROLE_USER)
                    .order_by("created_at", "id")
                    .first()
                )
                conv.title = (
                    first_user.content.strip()[:80] if first_user else "مکالمه جدید"
                )
            conv.updated_at = timezone.now()
            conv.save(update_fields=["title", "updated_at"])
    return conv


def project_to_dict(p: Project) -> dict:
    from projects.remote_server import public_status

    growth_summary = None
    try:
        from projects.growth_hub import get_or_create_hub

        hub = get_or_create_hub(p)
        growth_summary = {
            "lifecycle_stage": hub.lifecycle_stage,
            "production_url": hub.production_url or "",
        }
    except Exception:
        growth_summary = {"lifecycle_stage": "build", "production_url": ""}

    return {
        "id": p.id,
        "name": p.name,
        "root_path": p.root_path,
        "default_scope_paths": p.default_scope_paths,
        "always_context_paths": p.always_context_paths or [],
        "denied_content_paths": p.denied_content_paths or [],
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
        "conversation_count": p.conversations.count(),
        "remote_server": public_status(p),
        "growth_hub": growth_summary,
    }


def conversation_context_usage(c: Conversation) -> dict:
    model_id = resolve_model_id(c.llm_model or None)
    limit = model_context_window(model_id)
    used = estimate_history_tokens(c.to_history())
    remaining = max(0, limit - used)
    return {
        "model_id": model_id,
        "limit_tokens": limit,
        "used_tokens": used,
        "remaining_tokens": remaining,
        "full": used >= limit,
    }


def conversation_to_dict(c: Conversation, include_messages: bool = False) -> dict:
    data = {
        "id": c.id,
        "project_id": c.project_id,
        "agent_type": c.agent_type,
        "title": c.title,
        "topic_summary": c.topic_summary or c.title,
        "total_credits_used": str(c.total_credits_used or 0),
        "tool_trace": list(c.tool_trace or []),
        "scope_paths": c.scope_paths,
        "effective_scope_paths": c.effective_scope(),
        "scope_note": c.scope_note,
        "llm_model": resolve_model_id(c.llm_model or None),
        "context": conversation_context_usage(c),
        "created_at": c.created_at.isoformat(),
        "updated_at": c.updated_at.isoformat(),
        "message_count": c.messages.count(),
    }
    if include_messages:
        messages = c.messages.order_by("created_at", "id").annotate(
            has_backup=Exists(MessageBackup.objects.filter(message_id=OuterRef("pk")))
        )
        msg_list = list(messages)
        change_flags: dict[int, bool] = {}
        assistants_with_backup = None
        if any(m.role == ChatMessage.ROLE_ASSISTANT and m.has_backup for m in msg_list):
            assistants_with_backup = assistant_messages_with_backup(c)
        for m in msg_list:
            if m.role == ChatMessage.ROLE_ASSISTANT and m.has_backup:
                change_flags[m.id] = assistant_has_code_changes(
                    c, m, assistants_with_backup
                )
        data["messages"] = []
        for m in msg_list:
            item = {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "tool_steps": m.tool_steps,
                "created_at": m.created_at.isoformat(),
                "can_undo": m.role == ChatMessage.ROLE_ASSISTANT and bool(m.has_backup),
            }
            if m.role == ChatMessage.ROLE_ASSISTANT:
                item["has_code_changes"] = bool(change_flags.get(m.id))
                if item["has_code_changes"]:
                    item["changes_for_message_id"] = m.id
            data["messages"].append(item)
        data["timeline"] = build_conversation_timeline(c)
    return data
