from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("api/auth/login/", views.login_api, name="login_api"),
    path("api/auth/logout/", views.logout_api, name="logout_api"),
    path("", views.index, name="index"),
    path("tool/<str:public_id>/", views.tool_share_page, name="tool_share_page"),
    path("api/chat/", views.chat_api, name="chat_api"),
    path("api/chat/stream/", views.chat_stream, name="chat_stream"),
    path("api/chat/cancel/", views.chat_cancel, name="chat_cancel"),
    path("api/chat/permission/", views.chat_permission, name="chat_permission"),
    path("api/chat/user-input/", views.chat_user_input, name="chat_user_input"),
    path(
        "api/messages/<int:message_id>/undo-preview/",
        views.undo_message_preview,
        name="undo_message_preview",
    ),
    path("api/messages/<int:message_id>/undo/", views.undo_message, name="undo_message"),
    path(
        "api/messages/<int:message_id>/restore-file-preview/",
        views.restore_file_preview,
        name="restore_file_preview",
    ),
    path(
        "api/messages/<int:message_id>/restore-file/",
        views.restore_turn_file,
        name="restore_turn_file",
    ),
    path("api/health/", views.health, name="health"),
    path("api/workspace/tree/", views.workspace_tree, name="workspace_tree"),
    path("api/workspace/file/", views.workspace_file, name="workspace_file"),
]
