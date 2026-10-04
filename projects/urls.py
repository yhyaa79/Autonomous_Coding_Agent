from django.urls import path

from . import views

urlpatterns = [
    path("api/agents/", views.agent_types, name="agent_types"),
    path("api/billing/models/", views.billing_models_api, name="billing_models_api"),
    path("api/billing/wallet/", views.billing_wallet_api, name="billing_wallet_api"),
    path("api/user/llm-settings/", views.user_llm_settings_api, name="user_llm_settings_api"),
    path("api/user/file-access/", views.user_file_access_api, name="user_file_access_api"),
    path("api/projects/", views.project_list, name="project_list"),
    path("api/projects/create/", views.project_create, name="project_create"),
    path("api/projects/browse-dirs/", views.project_browse_dirs, name="project_browse_dirs"),
    path("api/projects/<int:project_id>/delete/", views.project_delete, name="project_delete"),
    path("api/projects/<int:project_id>/update/", views.project_update, name="project_update"),
    path(
        "api/projects/<int:project_id>/remote-server/",
        views.project_remote_server_api,
        name="project_remote_server_api",
    ),
    path(
        "api/projects/<int:project_id>/remote-server/test/",
        views.project_remote_server_test_api,
        name="project_remote_server_test_api",
    ),
    path(
        "api/projects/<int:project_id>/growth-hub/",
        views.project_growth_hub_api,
        name="project_growth_hub_api",
    ),
    path(
        "api/projects/<int:project_id>/debug-hub/",
        views.project_debug_hub_api,
        name="project_debug_hub_api",
    ),
    path(
        "api/projects/<int:project_id>/debug-hub/scan/",
        views.project_debug_scan_api,
        name="project_debug_scan_api",
    ),
    path(
        "api/projects/<int:project_id>/conversations/",
        views.conversation_list,
        name="conversation_list",
    ),
    path(
        "api/projects/<int:project_id>/conversations/create/",
        views.conversation_create,
        name="conversation_create",
    ),
    path(
        "api/conversations/<int:conversation_id>/",
        views.conversation_detail,
        name="conversation_detail",
    ),
    path(
        "api/conversations/<int:conversation_id>/update/",
        views.conversation_update,
        name="conversation_update",
    ),
    path(
        "api/conversations/<int:conversation_id>/delete/",
        views.conversation_delete,
        name="conversation_delete",
    ),
    path(
        "api/projects/<int:project_id>/jobs/",
        views.scheduled_job_list,
        name="scheduled_job_list",
    ),
    path(
        "api/projects/<int:project_id>/jobs/runs/",
        views.project_job_runs,
        name="project_job_runs",
    ),
    path(
        "api/projects/<int:project_id>/scheduler/tick/",
        views.scheduled_project_tick,
        name="scheduled_project_tick",
    ),
    path(
        "api/projects/<int:project_id>/jobs/create/",
        views.scheduled_job_create,
        name="scheduled_job_create",
    ),
    path(
        "api/jobs/<int:job_id>/detail/",
        views.scheduled_job_detail,
        name="scheduled_job_detail",
    ),
    path(
        "api/jobs/<int:job_id>/",
        views.scheduled_job_update,
        name="scheduled_job_update",
    ),
    path(
        "api/jobs/<int:job_id>/delete/",
        views.scheduled_job_delete,
        name="scheduled_job_delete",
    ),
    path(
        "api/jobs/<int:job_id>/runs/",
        views.scheduled_job_runs,
        name="scheduled_job_runs",
    ),
    path(
        "api/shared-tools/",
        views.shared_tool_library,
        name="shared_tool_library",
    ),
    path(
        "api/shared-tools/create/",
        views.shared_tool_create,
        name="shared_tool_create",
    ),
    path(
        "api/shared-tools/<str:public_id>/",
        views.shared_tool_detail,
        name="shared_tool_detail",
    ),
    path(
        "api/conversations/<int:conversation_id>/tools/",
        views.conversation_tools_list,
        name="conversation_tools_list",
    ),
    path(
        "api/conversations/<int:conversation_id>/tools/attach/",
        views.conversation_tool_attach,
        name="conversation_tool_attach",
    ),
    path(
        "api/conversations/<int:conversation_id>/tools/<str:public_id>/",
        views.conversation_tool_detach,
        name="conversation_tool_detach",
    ),
    path(
        "api/conversations/<int:conversation_id>/tools/by-id/<str:tool_id>/version/",
        views.conversation_tool_pin_version,
        name="conversation_tool_pin_version",
    ),
    path(
        "api/conversations/<int:conversation_id>/code-changes/",
        views.conversation_code_changes_api,
        name="conversation_code_changes",
    ),
    path(
        "api/messages/<int:message_id>/code-changes/",
        views.message_code_changes_api,
        name="message_code_changes",
    ),
]
