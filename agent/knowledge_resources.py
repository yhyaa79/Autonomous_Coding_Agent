from agent.options import AgentOptions
from agent.project_tools.validator import (
    ToolValidationError,
    normalize_source_body,
    validate_run_body,
    validate_tool_id,
)
from agent.tool_impl import tool_result
from projects.shared_tools import (
    auto_attach_after_create,
    create_knowledge_resource,
    create_new_version,
    get_family_by_tool_id,
    latest_version,
    normalize_content_blocks,
    register_shared_tool,
    tool_share_link,
)


def upsert_knowledge_resource(
    tool_id: str,
    description: str,
    content_kind: str,
    content_blocks: list | None,
    source_body: str,
    parameters: dict | None,
    display_name: str,
    new_version: bool,
    tags: list | None,
    options: AgentOptions,
) -> str:
    if not options.allow_write:
        return tool_result(False, "Write disabled (allow_write=false)")
    try:
        tid = validate_tool_id(tool_id)
    except ToolValidationError as exc:
        return tool_result(False, str(exc))

    blocks = normalize_content_blocks(content_blocks)
    body = normalize_source_body(source_body)
    tag_list = tags if isinstance(tags, list) else None
    kind_hint = (content_kind or "").strip().lower()
    if body and (kind_hint in ("", "code") or (not blocks and body)):
        try:
            validate_run_body(body)
        except ToolValidationError as exc:
            return tool_result(False, str(exc))
    family = get_family_by_tool_id(tid)
    if not family:
        try:
            version = create_knowledge_resource(
                tool_id=tid,
                display_name=(display_name or tid).strip(),
                description=(description or "").strip(),
                content_kind=(content_kind or "prompt").strip(),
                content_blocks=blocks,
                source_body=body,
                parameters=parameters or {},
                source_project_id=options.project_id,
                tags=tag_list,
            )
        except ToolValidationError as exc:
            return tool_result(False, str(exc))
    else:
        if not new_version and latest_version(family):
            return tool_result(
                False,
                f"منبع {tid} وجود دارد — new_version:true بفرستید تا ورژن بعدی ساخته شود.",
            )
        try:
            if body and (content_kind or "code") == "code":
                version = register_shared_tool(
                    tool_id=tid,
                    display_name=family.display_name,
                    description=(description or "").strip(),
                    parameters=parameters or {},
                    source_body=body,
                    source_project_id=options.project_id,
                    content_blocks=blocks,
                    content_kind="code",
                    new_version=True,
                    tags=tag_list,
                )
            else:
                version = create_new_version(
                    family,
                    description=(description or "").strip(),
                    parameters=parameters or {},
                    source_body=body,
                    content_blocks=blocks,
                    content_kind=content_kind or "prompt",
                    tags=tag_list,
                )
        except ToolValidationError as exc:
            return tool_result(False, str(exc))

    auto_attach_after_create(options, version)
    link = tool_share_link(
        version.public_id,
        conversation_id=options.conversation_id,
        project_id=options.project_id,
    )
    return tool_result(
        True,
        f"منبع {tid} v{version.version_number} ({version.content_kind}) ثبت شد.\nلینک: {link}",
    )
