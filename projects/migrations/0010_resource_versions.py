# Resource library versioning

import django.db.models.deletion
from django.db import migrations, models


def migrate_shared_tools_to_versions(apps, schema_editor):
    SharedTool = apps.get_model("projects", "SharedTool")
    SharedToolVersion = apps.get_model("projects", "SharedToolVersion")
    for tool in SharedTool.objects.all():
        body = (getattr(tool, "source_body", None) or "").strip()
        kind = "code" if body else "prompt"
        SharedToolVersion.objects.create(
            shared_tool_id=tool.id,
            version_number=1,
            public_id=tool.public_id,
            content_kind=kind,
            description=getattr(tool, "description", "") or "",
            parameters=getattr(tool, "parameters", None) or {},
            source_body=getattr(tool, "source_body", "") or "",
            content_blocks=[],
        )


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0009_conversation_feed_and_ui_state"),
    ]

    operations = [
        migrations.CreateModel(
            name="SharedToolVersion",
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
                ("version_number", models.PositiveIntegerField()),
                ("public_id", models.CharField(db_index=True, max_length=36, unique=True)),
                (
                    "content_kind",
                    models.CharField(
                        choices=[
                            ("code", "code"),
                            ("prompt", "prompt"),
                            ("link", "link"),
                            ("image", "image"),
                            ("video", "video"),
                            ("audio", "audio"),
                            ("mixed", "mixed"),
                        ],
                        default="code",
                        max_length=16,
                    ),
                ),
                ("description", models.TextField(blank=True, default="")),
                ("parameters", models.JSONField(blank=True, default=dict)),
                ("source_body", models.TextField(blank=True, default="")),
                ("content_blocks", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "shared_tool",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="versions",
                        to="projects.sharedtool",
                    ),
                ),
            ],
            options={
                "ordering": ["-version_number", "-id"],
            },
        ),
        migrations.AddConstraint(
            model_name="sharedtoolversion",
            constraint=models.UniqueConstraint(
                fields=("shared_tool", "version_number"),
                name="uniq_shared_tool_version_number",
            ),
        ),
        migrations.RunPython(migrate_shared_tools_to_versions, migrations.RunPython.noop),
        migrations.RemoveField(model_name="sharedtool", name="description"),
        migrations.RemoveField(model_name="sharedtool", name="parameters"),
        migrations.RemoveField(model_name="sharedtool", name="public_id"),
        migrations.RemoveField(model_name="sharedtool", name="source_body"),
        migrations.AlterField(
            model_name="sharedtool",
            name="tool_id",
            field=models.CharField(db_index=True, max_length=64, unique=True),
        ),
        migrations.AddField(
            model_name="conversationsharedtool",
            name="pinned_version",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="conversation_pins",
                to="projects.sharedtoolversion",
            ),
        ),
    ]
