"""بارگذاری side-effect همهٔ ابزارها و API عمومی."""

from agent.tool_registry import all_tool_definitions, all_tool_ids

_loaded = False


def ensure_tools_loaded() -> None:
    global _loaded
    if _loaded:
        return
    from . import (  # noqa: F401
        ask_user,
        analyze_content_keywords,
        analyze_html_seo,
        apply_patch,
        apply_unified_diff,
        audit_site_seo_basics,
        cancel_scheduled_job,
        checkpoint_create,
        checkpoint_restore,
        create_project_tool,
        delete_file,
        format_lint,
        git_commit,
        git_diff,
        git_log,
        git_status,
        glob_files,
        instagram_login,
        instagram_post_story,
        list_directory,
        list_project_tools,
        list_scheduled_jobs,
        move_file,
        project_note,
        project_tree,
        read_file,
        run_shell,
        run_tests,
        save_seo_report,
        schedule_job,
        search_code,
        telegram_login,
        test_project_tool,
        update_growth_hub,
        upsert_knowledge_resource,
        web_fetch,
        write_file,
    )

    _loaded = True


__all__ = ["ensure_tools_loaded", "all_tool_ids", "all_tool_definitions"]
