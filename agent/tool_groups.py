"""گروه‌بندی ابزارها برای agentهای مختلف."""

WORKSPACE_TOOLS: tuple[str, ...] = (
    "ask_user",
    "project_tree",
    "list_directory",
    "glob_files",
    "search_code",
    "read_file",
    "apply_patch",
    "apply_unified_diff",
    "write_file",
    "delete_file",
    "move_file",
    "run_shell",
)

CODING_TOOLS: tuple[str, ...] = (
    "git_status",
    "git_diff",
    "git_log",
    "git_commit",
    "run_tests",
    "format_lint",
    "web_fetch",
    "project_note",
    "checkpoint_create",
    "checkpoint_restore",
)

SEO_TOOLS: tuple[str, ...] = (
    "analyze_html_seo",
    "audit_site_seo_basics",
    "analyze_content_keywords",
    "save_seo_report",
)

SCHEDULE_TOOLS: tuple[str, ...] = (
    "schedule_job",
    "list_scheduled_jobs",
    "cancel_scheduled_job",
)

SOCIAL_TOOLS: tuple[str, ...] = (
    "telegram_login",
    "instagram_login",
    "instagram_post_story",
)

META_PROJECT_TOOLS: tuple[str, ...] = (
    "create_project_tool",
    "list_project_tools",
    "test_project_tool",
    "upsert_knowledge_resource",
)

GROWTH_HUB_TOOLS: tuple[str, ...] = ("update_growth_hub",)


def coding_tool_ids() -> tuple[str, ...]:
    return tuple(
        dict.fromkeys((*WORKSPACE_TOOLS, *CODING_TOOLS, *SCHEDULE_TOOLS, *META_PROJECT_TOOLS))
    )


def seo_tool_ids() -> tuple[str, ...]:
    read = ("project_tree", "list_directory", "glob_files", "search_code", "read_file", "web_fetch")
    return tuple(dict.fromkeys((*read, *SEO_TOOLS, *SCHEDULE_TOOLS)))


def social_tool_ids() -> tuple[str, ...]:
    light = ("read_file", "list_directory", "project_note")
    return tuple(dict.fromkeys((*light, *SOCIAL_TOOLS, *SCHEDULE_TOOLS)))


def maintenance_tool_ids() -> tuple[str, ...]:
    read = ("project_tree", "list_directory", "glob_files", "search_code", "read_file")
    ops = (
        "run_shell",
        "run_tests",
        "web_fetch",
        "git_status",
        "git_diff",
        "checkpoint_create",
    )
    return tuple(
        dict.fromkeys((*read, *ops, *SCHEDULE_TOOLS, *GROWTH_HUB_TOOLS, "project_note"))
    )


def marketing_tool_ids() -> tuple[str, ...]:
    read = ("project_tree", "list_directory", "glob_files", "search_code", "read_file", "web_fetch")
    write = ("write_file", "apply_patch")
    return tuple(
        dict.fromkeys(
            (
                *read,
                *write,
                *SEO_TOOLS,
                *SOCIAL_TOOLS,
                *SCHEDULE_TOOLS,
                *GROWTH_HUB_TOOLS,
                *META_PROJECT_TOOLS,
                "project_note",
            )
        )
    )


def autonomous_tool_ids() -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            (
                *WORKSPACE_TOOLS,
                *CODING_TOOLS,
                *SEO_TOOLS,
                *SCHEDULE_TOOLS,
                *SOCIAL_TOOLS,
                *GROWTH_HUB_TOOLS,
                *META_PROJECT_TOOLS,
            )
        )
    )


def debug_tool_ids() -> tuple[str, ...]:
    seo_light = ("analyze_html_seo", "audit_site_seo_basics")
    return tuple(
        dict.fromkeys(
            (
                *WORKSPACE_TOOLS,
                "run_tests",
                "format_lint",
                "web_fetch",
                "git_status",
                "git_diff",
                "project_note",
                "checkpoint_create",
                *seo_light,
            )
        )
    )
