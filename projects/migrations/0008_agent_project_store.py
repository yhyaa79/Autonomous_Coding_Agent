# Lightweight agent data in the database. Heavy files stay in <project>/.aca/.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0007_billing_user_wallet"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectMemory",
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
                ("content", models.TextField(blank=True, default="")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memory",
                        to="projects.project",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ProjectDebugState",
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
                ("attempts", models.JSONField(blank=True, default=list)),
                ("last_recovery", models.TextField(blank=True, default="")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="debug_state",
                        to="projects.project",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ProjectSession",
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
                ("kind", models.CharField(max_length=32)),
                ("account_key", models.CharField(max_length=200)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_sessions",
                        to="projects.project",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ProjectTool",
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
                ("tool_id", models.CharField(max_length=64)),
                ("description", models.TextField(blank=True, default="")),
                ("parameters", models.JSONField(blank=True, default=dict)),
                ("source_body", models.TextField(blank=True, default="")),
                ("module_source", models.TextField(blank=True, default="")),
                ("shared_public_id", models.CharField(blank=True, default="", max_length=36)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="project_tools",
                        to="projects.project",
                    ),
                ),
            ],
            options={
                "ordering": ["tool_id"],
            },
        ),
        migrations.AddConstraint(
            model_name="projectsession",
            constraint=models.UniqueConstraint(
                fields=("project", "kind", "account_key"),
                name="uniq_project_agent_session",
            ),
        ),
        migrations.AddConstraint(
            model_name="projecttool",
            constraint=models.UniqueConstraint(
                fields=("project", "tool_id"),
                name="uniq_project_tool",
            ),
        ),
    ]
