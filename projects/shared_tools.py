"""کتابخانهٔ منابع (ورژن‌دار) و اتصال به مکالمه."""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any

from django.conf import settings
from django.db import transaction
from django.db.models import Max

from agent.options import AgentOptions
from agent.project_tools.loader import invalidate_project_cache
from agent.project_tools.service import _read_manifest, _write_manifest
from agent.project_tools.template import build_module_source
from agent.project_tools.paths import tool_module_path
from agent.project_tools.validator import ToolValidationError, validate_tool_id

from .models import (
    Conversation,
    ConversationSharedTool,
    SharedTool,
    SharedToolVersion,
)
from .resource_tags import normalize_resource_tags, tag_label_fa

_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
    re.I,
)
_ACA_PREFIX = re.compile(r"^aca-tool:\s*", re.I)
_SLUG_RE = re.compile(r"^[a-z][a-z0-9_]{1,62}$")


def parse_public_ref(raw: str) -> str | None:
    """شناسهٔ عمومی را از لینک، UUID خام، یا aca-tool: استخراج می‌کند."""
    text = (raw or "").strip()
    if not text:
        return None
    text = _ACA_PREFIX.sub("", text)
    match = _UUID_RE.search(text)
    if match:
        return match.group(0).lower()
    return None


def tool_share_path(
    public_id: str,
    *,
    conversation_id: int | None = None,
    project_id: int | None = None,
) -> str:
    path = f"/tool/{public_id}/"
    params: list[str] = []
    if conversation_id:
        params.append(f"conversation_id={int(conversation_id)}")
    if project_id:
        params.append(f"project_id={int(project_id)}")
    if params:
        path += "?" + "&".join(params)
    return path


def tool_share_link(
    public_id: str,
    request=None,
    *,
    conversation_id: int | None = None,
    project_id: int | None = None,
) -> str:
    base = getattr(settings, "ACA_PUBLIC_BASE_URL", "").rstrip("/")
    if not base and request is not None:
        try:
            base = request.build_absolute_uri("/").rstrip("/")
        except Exception:
            base = ""
    if not base:
        base = "http://127.0.0.1:8000"
    return f"{base}{tool_share_path(public_id, conversation_id=conversation_id, project_id=project_id)}"


def _infer_content_kind(
    *,
    content_kind: str | None,
    source_body: str,
    content_blocks: list[Any] | None,
) -> str:
    if content_kind and content_kind in dict(SharedToolVersion.KIND_CHOICES):
        return content_kind
    blocks = content_blocks or []
    if (source_body or "").strip():
        return SharedToolVersion.KIND_CODE
    if not blocks:
        return SharedToolVersion.KIND_PROMPT
    kinds = {str(b.get("type") or "") for b in blocks if isinstance(b, dict)}
    if len(kinds) == 1:
        t = next(iter(kinds))
        mapping = {
            "text": SharedToolVersion.KIND_PROMPT,
            "prompt": SharedToolVersion.KIND_PROMPT,
            "code": SharedToolVersion.KIND_CODE,
            "link": SharedToolVersion.KIND_LINK,
            "image": SharedToolVersion.KIND_IMAGE,
            "video": SharedToolVersion.KIND_VIDEO,
            "audio": SharedToolVersion.KIND_AUDIO,
        }
        return mapping.get(t, SharedToolVersion.KIND_MIXED)
    return SharedToolVersion.KIND_MIXED


def normalize_content_blocks(blocks: Any) -> list[dict[str, Any]]:
    if not isinstance(blocks, list):
        return []
    out: list[dict[str, Any]] = []
    for item in blocks:
        if not isinstance(item, dict):
            continue
        btype = str(item.get("type") or "text").strip().lower()
        if btype in ("text", "prompt"):
            text = str(item.get("text") or item.get("body") or "").strip()
            if text:
                out.append({"type": "text", "text": text})
        elif btype == "code":
            out.append(
                {
                    "type": "code",
                    "language": str(item.get("language") or "python"),
                    "text": str(item.get("text") or item.get("body") or ""),
                }
            )
        elif btype == "link":
            url = str(item.get("url") or "").strip()
            if url:
                out.append(
                    {
                        "type": "link",
                        "url": url,
                        "label": str(item.get("label") or item.get("title") or url),
                    }
                )
        elif btype in ("image", "video", "audio"):
            url = str(item.get("url") or "").strip()
            if url:
                out.append({"type": btype, "url": url, "caption": str(item.get("caption") or "")})
    return out


def get_version_by_public_id(public_id: str) -> SharedToolVersion | None:
    ref = parse_public_ref(public_id) or (public_id or "").strip().lower()
    if not ref:
        return None
    return (
        SharedToolVersion.objects.select_related("shared_tool")
        .filter(public_id=ref)
        .first()
    )


def get_family_by_tool_id(tool_id: str) -> SharedTool | None:
    tid = (tool_id or "").strip()
    if not tid:
        return None
    return SharedTool.objects.filter(tool_id=tid).first()


def latest_version(family: SharedTool) -> SharedToolVersion | None:
    return family.versions.order_by("-version_number", "-id").first()


def effective_version(
    family: SharedTool,
    pinned: SharedToolVersion | None = None,
) -> SharedToolVersion | None:
    if pinned and pinned.shared_tool_id == family.id:
        return pinned
    return latest_version(family)


def version_to_dict(
    version: SharedToolVersion,
    *,
    request=None,
    include_source: bool = False,
    conversation_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]:
    family = version.shared_tool
    data: dict[str, Any] = {
        "public_id": version.public_id,
        "version_number": version.version_number,
        "tool_id": family.tool_id,
        "display_name": family.display_name,
        "content_kind": version.content_kind,
        "description": version.description,
        "parameters": version.parameters,
        "content_blocks": version.content_blocks or [],
        "share_link": tool_share_link(
            version.public_id,
            request,
            conversation_id=conversation_id,
            project_id=project_id,
        ),
        "created_at": version.created_at.isoformat(),
    }
    if include_source:
        data["source_body"] = version.source_body
    return data


def shared_tool_to_dict(
    family: SharedTool,
    *,
    request=None,
    include_source: bool = False,
    link: ConversationSharedTool | None = None,
    version: SharedToolVersion | None = None,
    conversation_id: int | None = None,
    project_id: int | None = None,
) -> dict[str, Any]:
    pinned = link.pinned_version if link else None
    active = version or effective_version(family, pinned)
    latest = latest_version(family)
    if not active or not latest:
        return {
            "tool_id": family.tool_id,
            "display_name": family.display_name,
            "version_count": 0,
        }
    base = version_to_dict(
        active,
        request=request,
        include_source=include_source,
        conversation_id=conversation_id,
        project_id=project_id,
    )
    tags = normalize_resource_tags(family.tags)
    base.update(
        {
            "tags": tags,
            "tag_labels": [tag_label_fa(t) for t in tags],
            "latest_public_id": latest.public_id,
            "latest_version_number": latest.version_number,
            "pinned_public_id": pinned.public_id if pinned else None,
            "pinned_version_number": pinned.version_number if pinned else None,
            "version_count": family.versions.count(),
            "versions_brief": list_versions_for_family(family),
            "updated_at": family.updated_at.isoformat(),
            "created_at": family.created_at.isoformat(),
            "source_project_id": family.source_project_id,
        }
    )
    return base


def list_versions_for_family(family: SharedTool) -> list[dict[str, Any]]:
    return [
        {
            "public_id": v.public_id,
            "version_number": v.version_number,
            "content_kind": v.content_kind,
            "description": (v.description or "")[:300],
            "created_at": v.created_at.isoformat(),
        }
        for v in family.versions.order_by("-version_number", "-id")
    ]


def _next_version_number(family: SharedTool) -> int:
    current = family.versions.aggregate(m=Max("version_number"))["m"]
    return int(current or 0) + 1


def apply_family_tags(family: SharedTool, tags: Any | None) -> None:
    normalized = normalize_resource_tags(tags)
    if not normalized:
        return
    current = normalize_resource_tags(family.tags)
    merged = list(current)
    for t in normalized:
        if t not in merged:
            merged.append(t)
    if merged != current:
        family.tags = merged
        family.save(update_fields=["tags", "updated_at"])


def create_new_version(
    family: SharedTool,
    *,
    description: str,
    parameters: dict[str, Any] | None,
    source_body: str,
    content_blocks: list[dict[str, Any]] | None = None,
    content_kind: str | None = None,
    tags: Any | None = None,
) -> SharedToolVersion:
    blocks = normalize_content_blocks(content_blocks)
    body = (source_body or "").strip()
    kind = _infer_content_kind(content_kind=content_kind, source_body=body, content_blocks=blocks)
    if kind == SharedToolVersion.KIND_CODE and not body:
        raise ToolValidationError("برای منبع از نوع code، source_body الزامی است")
    version = SharedToolVersion.objects.create(
        shared_tool=family,
        version_number=_next_version_number(family),
        public_id=str(uuid.uuid4()),
        content_kind=kind,
        description=(description or "").strip()[:2000],
        parameters=parameters or {},
        source_body=body,
        content_blocks=blocks,
    )
    apply_family_tags(family, tags)
    family.save(update_fields=["updated_at"])
    return version


def register_shared_tool(
    *,
    tool_id: str,
    display_name: str,
    description: str,
    parameters: dict[str, Any],
    source_body: str,
    source_project_id: int | None = None,
    content_blocks: list[dict[str, Any]] | None = None,
    content_kind: str | None = None,
    new_version: bool = False,
    tags: Any | None = None,
) -> SharedToolVersion:
    tid = validate_tool_id(tool_id)
    name = (display_name or tid).strip()[:200] or tid
    family = SharedTool.objects.filter(tool_id=tid).first()
    if not family:
        family = SharedTool.objects.create(
            tool_id=tid,
            display_name=name,
            source_project_id=source_project_id,
        )
    elif new_version:
        pass
    else:
        if family.display_name != name and name != tid:
            family.display_name = name
            family.save(update_fields=["display_name", "updated_at"])
        if source_project_id and not family.source_project_id:
            family.source_project_id = source_project_id
            family.save(update_fields=["source_project_id", "updated_at"])

    if family.versions.exists() and not new_version:
        new_version = True

    return create_new_version(
        family,
        description=description,
        parameters=parameters,
        source_body=source_body,
        content_blocks=content_blocks,
        content_kind=content_kind,
        tags=tags,
    )


def create_knowledge_resource(
    *,
    tool_id: str,
    display_name: str,
    description: str,
    content_kind: str,
    content_blocks: list[dict[str, Any]] | None = None,
    source_body: str = "",
    parameters: dict[str, Any] | None = None,
    source_project_id: int | None = None,
    tags: Any | None = None,
) -> SharedToolVersion:
    if SharedTool.objects.filter(tool_id=validate_tool_id(tool_id)).exists():
        raise ToolValidationError(
            f"منبع با شناسه {tool_id} از قبل وجود دارد — برای ورژن جدید new_version:true بفرستید."
        )
    family = SharedTool.objects.create(
        tool_id=validate_tool_id(tool_id),
        display_name=(display_name or tool_id).strip()[:200],
        source_project_id=source_project_id,
        tags=normalize_resource_tags(tags),
    )
    return create_new_version(
        family,
        description=description,
        parameters=parameters or {},
        source_body=source_body,
        content_blocks=content_blocks,
        content_kind=content_kind,
        tags=tags,
    )


def install_shared_tool_on_workspace(
    version: SharedToolVersion,
    workspace: Path,
    project_id: int | None = None,
) -> None:
    """فایل اجرایی داخل پوشهٔ ایجنت را برای ورژن code همگام می‌کند."""
    family = version.shared_tool
    tid = family.tool_id
    if version.content_kind != SharedToolVersion.KIND_CODE or not (version.source_body or "").strip():
        return
    mod_path = tool_module_path(workspace, tid)
    mod_path.parent.mkdir(parents=True, exist_ok=True)
    full_source = build_module_source(version.source_body)
    mod_path.write_text(full_source, encoding="utf-8")
    if project_id:
        from agent.project_data import upsert_project_tool

        upsert_project_tool(
            project_id=project_id,
            tool_id=tid,
            description=(version.description or family.display_name or tid),
            parameters=version.parameters
            or {"type": "object", "properties": {}, "required": []},
            source_body=version.source_body,
            shared_public_id=version.public_id,
            module_source="",
        )

    manifest = _read_manifest(workspace)
    tools = manifest.get("tools")
    if not isinstance(tools, list):
        tools = []
    entry = {
        "id": tid,
        "description": (version.description or family.display_name or tid)[:500],
        "parameters": version.parameters
        or {"type": "object", "properties": {}, "required": []},
        "shared_public_id": version.public_id,
    }
    replaced = False
    for i, item in enumerate(tools):
        if isinstance(item, dict) and str(item.get("id") or "") == tid:
            tools[i] = entry
            replaced = True
            break
    if not replaced:
        tools.append(entry)
    manifest["tools"] = tools
    _write_manifest(workspace, manifest)


def attach_shared_tool_to_conversation(
    conv: Conversation,
    family: SharedTool,
    *,
    pinned_version: SharedToolVersion | None = None,
    sync_workspace: bool = True,
) -> ConversationSharedTool:
    with transaction.atomic():
        link, _created = ConversationSharedTool.objects.get_or_create(
            conversation=conv,
            shared_tool=family,
        )
        if pinned_version and pinned_version.shared_tool_id == family.id:
            link.pinned_version = pinned_version
            link.save(update_fields=["pinned_version"])
        version = effective_version(family, link.pinned_version)
        if sync_workspace and conv.project_id and version:
            workspace = Path(conv.project.root_path)
            install_shared_tool_on_workspace(version, workspace, project_id=conv.project_id)
            invalidate_project_cache(conv.project_id, workspace)
        return link


def set_conversation_resource_version(
    conv: Conversation,
    tool_id: str,
    *,
    version_public_id: str | None,
    sync_workspace: bool = True,
) -> ConversationSharedTool:
    family = get_object_or_404_tool(tool_id)
    link = ConversationSharedTool.objects.filter(conversation=conv, shared_tool=family).first()
    if not link:
        raise ValueError("این منبع به مکالمه وصل نیست")
    pinned: SharedToolVersion | None = None
    if version_public_id:
        pinned = get_version_by_public_id(version_public_id)
        if not pinned or pinned.shared_tool_id != family.id:
            raise ValueError("ورژن انتخاب‌شده برای این منبع معتبر نیست")
    link.pinned_version = pinned
    link.save(update_fields=["pinned_version"])
    version = effective_version(family, pinned)
    if sync_workspace and conv.project_id and version:
        workspace = Path(conv.project.root_path)
        install_shared_tool_on_workspace(version, workspace, project_id=conv.project_id)
        invalidate_project_cache(conv.project_id, workspace)
    return link


def get_object_or_404_tool(tool_id: str) -> SharedTool:
    family = get_family_by_tool_id(tool_id)
    if not family:
        raise ValueError("منبع پیدا نشد")
    return family


def detach_shared_tool_from_conversation(conv: Conversation, public_id: str) -> bool:
    ref = parse_public_ref(public_id) or public_id.strip().lower()
    version = get_version_by_public_id(ref)
    if version:
        deleted, _ = ConversationSharedTool.objects.filter(
            conversation=conv,
            shared_tool_id=version.shared_tool_id,
        ).delete()
        return deleted > 0
    family = get_family_by_tool_id(ref)
    if family:
        deleted, _ = ConversationSharedTool.objects.filter(
            conversation=conv,
            shared_tool=family,
        ).delete()
        return deleted > 0
    deleted, _ = ConversationSharedTool.objects.filter(
        conversation=conv,
        shared_tool__tool_id=ref,
    ).delete()
    return deleted > 0


def attach_by_public_ref(conv: Conversation, raw: str) -> SharedToolVersion:
    public_id = parse_public_ref(raw)
    slug = (raw or "").strip()
    pinned: SharedToolVersion | None = None
    family: SharedTool | None = None
    if public_id:
        pinned = get_version_by_public_id(public_id)
        if pinned:
            family = pinned.shared_tool
    if not family and _SLUG_RE.match(slug):
        family = get_family_by_tool_id(slug)
    if not family:
        raise ValueError("لینک، شناسه یا slug منبع معتبر نیست")
    if not pinned:
        pinned = latest_version(family)
    if not pinned:
        raise ValueError("این منبع هنوز ورژنی ندارد")
    attach_shared_tool_to_conversation(conv, family, pinned_version=pinned)
    return pinned


def list_conversation_shared_tools(conv: Conversation) -> list[tuple[SharedTool, ConversationSharedTool]]:
    links = (
        ConversationSharedTool.objects.filter(conversation=conv)
        .select_related("shared_tool", "pinned_version")
        .order_by("shared_tool__display_name", "shared_tool__tool_id")
    )
    return [(link.shared_tool, link) for link in links]


def list_project_shared_tools(project_id: int) -> list[SharedTool]:
    return list(
        SharedTool.objects.filter(source_project_id=project_id).order_by("-updated_at")
    )


def list_all_shared_tools(limit: int = 300) -> list[SharedTool]:
    cap = max(1, min(int(limit), 500))
    return list(SharedTool.objects.all().order_by("-updated_at")[:cap])


def delete_shared_tool(public_id: str) -> bool:
    ref = parse_public_ref(public_id) or (public_id or "").strip().lower()
    version = get_version_by_public_id(ref)
    if version:
        family = version.shared_tool
        version.delete()
        if not family.versions.exists():
            family.delete()
        return True
    family = get_family_by_tool_id(ref)
    if family:
        family.delete()
        return True
    return False


def delete_resource_family(tool_id: str) -> bool:
    family = get_family_by_tool_id(tool_id)
    if not family:
        return False
    family.delete()
    return True


def auto_attach_after_create(
    options: AgentOptions,
    version: SharedToolVersion,
) -> None:
    if not options.conversation_id:
        return
    conv = Conversation.objects.filter(pk=options.conversation_id).first()
    if conv:
        attach_shared_tool_to_conversation(
            conv, version.shared_tool, pinned_version=version, sync_workspace=False
        )


def definition_for_shared_tool(version: SharedToolVersion) -> dict[str, Any]:
    family = version.shared_tool
    desc = version.description or family.display_name or family.tool_id
    params = version.parameters or {"type": "object", "properties": {}, "required": []}
    ver_tag = f"v{version.version_number}"
    return {
        "type": "function",
        "function": {
            "name": family.tool_id,
            "description": f"[کتابخانه {ver_tag}] {desc}",
            "parameters": params,
        },
    }


def attached_tool_ids_for_conversation(conversation_id: int | None) -> set[str]:
    if not conversation_id:
        return set()
    return set(
        SharedTool.objects.filter(
            conversation_links__conversation_id=conversation_id
        ).values_list("tool_id", flat=True)
    )


def conversation_resource_context(conversation_id: int | None) -> str:
    """متن منابع غیراجرایی متصل به مکالمه برای system prompt."""
    if not conversation_id:
        return ""
    lines: list[str] = []
    for family, link in list_conversation_shared_tools(
        Conversation.objects.get(pk=conversation_id)
    ):
        version = effective_version(family, link.pinned_version)
        if not version:
            continue
        if version.content_kind == SharedToolVersion.KIND_CODE and (version.source_body or "").strip():
            continue
        tag_str = ", ".join(normalize_resource_tags(family.tags))
        header = (
            f"### {family.display_name} ({family.tool_id}) — v{version.version_number}"
            + (f" [{tag_str}]" if tag_str else "")
        )
        parts = [header]
        if version.description:
            parts.append(version.description.strip())
        for block in version.content_blocks or []:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "text":
                parts.append(str(block.get("text") or ""))
            elif btype == "code":
                parts.append(
                    f"```{block.get('language') or ''}\n{block.get('text') or ''}\n```"
                )
            elif btype == "link":
                parts.append(f"Link: {block.get('label') or ''} → {block.get('url') or ''}")
            elif btype in ("image", "video", "audio"):
                cap = block.get("caption") or btype
                parts.append(f"{cap}: {block.get('url') or ''}")
        if len(parts) > 1:
            lines.append("\n".join(p for p in parts if p))
    if not lines:
        return ""
    return "Attached knowledge resources (follow when relevant):\n\n" + "\n\n---\n\n".join(lines)


def ensure_shared_tool_from_project_row(row: Any) -> SharedToolVersion | None:
    """ProjectTool را در کتابخانهٔ SharedTool همگام می‌کند (برای نمایش در UI)."""
    from .models import ProjectTool

    if not isinstance(row, ProjectTool):
        return None
    tid = (row.tool_id or "").strip()
    if not tid:
        return None
    pinned: SharedToolVersion | None = None
    pub = (row.shared_public_id or "").strip()
    if pub:
        pinned = get_version_by_public_id(pub)
    family = get_family_by_tool_id(tid)
    if pinned and pinned.shared_tool.tool_id == tid:
        return pinned
    if family and latest_version(family):
        return latest_version(family)
    body = (row.source_body or "").strip()
    if not body:
        return latest_version(family) if family else None
    try:
        version = register_shared_tool(
            tool_id=tid,
            display_name=tid,
            description=(row.description or tid).strip(),
            parameters=row.parameters if isinstance(row.parameters, dict) else {},
            source_body=body,
            source_project_id=row.project_id,
            content_kind="code",
            new_version=bool(family),
            tags=["ops"],
        )
        if not (row.shared_public_id or "").strip():
            row.shared_public_id = version.public_id
            row.save(update_fields=["shared_public_id", "updated_at"])
        return version
    except ToolValidationError:
        return latest_version(family) if family else None


def sync_project_tools_into_library(project_id: int | None = None) -> None:
    from .models import ProjectTool

    qs = ProjectTool.objects.all()
    if project_id:
        qs = qs.filter(project_id=project_id)
    for row in qs.iterator():
        ensure_shared_tool_from_project_row(row)


def list_tools_for_conversation_ui(conv: Conversation, request=None) -> list[dict[str, Any]]:
    """فقط منابعی که به این مکالمه متصل شده‌اند."""
    tools: list[dict[str, Any]] = []
    for family, link in list_conversation_shared_tools(conv):
        data = shared_tool_to_dict(
            family,
            request=request,
            link=link,
            conversation_id=conv.id,
            project_id=conv.project_id,
        )
        data["attached_to_conversation"] = True
        tools.append(data)
    return tools


def list_tools_for_library(request=None, limit: int = 300) -> tuple[list[dict[str, Any]], int]:
    sync_project_tools_into_library()
    cap = max(1, min(int(limit), 500))
    families = list_all_shared_tools(cap)
    total = SharedTool.objects.count()
    tools: list[dict[str, Any]] = []
    for family in families:
        try:
            tools.append(shared_tool_to_dict(family, request=request))
        except Exception:
            tools.append(
                {
                    "tool_id": family.tool_id,
                    "display_name": family.display_name,
                    "description": "—",
                    "version_count": 0,
                    "tags": normalize_resource_tags(family.tags),
                }
            )
    return tools, total


def update_version_from_payload(
    base_version: SharedToolVersion,
    payload: dict[str, Any],
) -> SharedToolVersion:
    """ورژن جدید از روی payload (نام خانواده ثابت می‌ماند)."""
    family = base_version.shared_tool
    desc = str(payload.get("description") if "description" in payload else base_version.description)
    params = payload.get("parameters")
    if params is None:
        params = base_version.parameters
    source = str(payload.get("source_body") if "source_body" in payload else base_version.source_body)
    blocks = payload.get("content_blocks")
    if blocks is None:
        blocks = base_version.content_blocks
    kind = payload.get("content_kind") or base_version.content_kind
    return create_new_version(
        family,
        description=desc,
        parameters=params if isinstance(params, dict) else {},
        source_body=source,
        content_blocks=blocks if isinstance(blocks, list) else [],
        content_kind=str(kind),
    )
