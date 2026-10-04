# Generated manually for shared tool library

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0005_message_backup"),
    ]

    operations = [
        migrations.CreateModel(
            name="SharedTool",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("public_id", models.CharField(db_index=True, max_length=36, unique=True)),
                ("display_name", models.CharField(max_length=200)),
                ("tool_id", models.CharField(db_index=True, max_length=64)),
                ("description", models.TextField(blank=True, default="")),
                ("parameters", models.JSONField(blank=True, default=dict)),
                ("source_body", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "source_project",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="shared_tools_created",
                        to="projects.project",
                    ),
                ),
            ],
            options={
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="ConversationSharedTool",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                (
                    "conversation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shared_tool_links",
                        to="projects.conversation",
                    ),
                ),
                (
                    "shared_tool",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="conversation_links",
                        to="projects.sharedtool",
                    ),
                ),
            ],
            options={
                "ordering": ["added_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="conversationsharedtool",
            constraint=models.UniqueConstraint(
                fields=("conversation", "shared_tool"),
                name="uniq_conversation_shared_tool",
            ),
        ),
    ]
