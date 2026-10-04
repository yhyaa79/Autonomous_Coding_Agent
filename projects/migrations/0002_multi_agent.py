# Generated manually for multi-agent platform

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="conversation",
            name="agent_type",
            field=models.CharField(
                choices=[
                    ("coding", "coding"),
                    ("seo", "seo"),
                    ("scheduler", "scheduler"),
                ],
                default="coding",
                max_length=32,
            ),
        ),
        migrations.CreateModel(
            name="ScheduledJob",
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
                ("created_by_agent_type", models.CharField(default="coding", max_length=32)),
                ("target_agent_type", models.CharField(default="coding", max_length=32)),
                ("title", models.CharField(max_length=200)),
                ("payload", models.JSONField(blank=True, default=dict)),
                (
                    "schedule_kind",
                    models.CharField(
                        choices=[
                            ("once", "once"),
                            ("cron", "cron"),
                            ("interval", "interval"),
                        ],
                        max_length=16,
                    ),
                ),
                ("run_at", models.DateTimeField(blank=True, null=True)),
                ("cron_expression", models.CharField(blank=True, default="", max_length=120)),
                ("interval_seconds", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "timezone_name",
                    models.CharField(blank=True, default="Asia/Tehran", max_length=64),
                ),
                ("next_run_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("last_run_at", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "active"),
                            ("paused", "paused"),
                            ("completed", "completed"),
                            ("cancelled", "cancelled"),
                        ],
                        default="active",
                        max_length=16,
                    ),
                ),
                ("max_runs", models.PositiveIntegerField(blank=True, null=True)),
                ("run_count", models.PositiveIntegerField(default=0)),
                ("last_error", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scheduled_jobs",
                        to="projects.project",
                    ),
                ),
                (
                    "source_conversation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="scheduled_jobs",
                        to="projects.conversation",
                    ),
                ),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="JobRun",
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
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("running", "running"),
                            ("success", "success"),
                            ("failed", "failed"),
                        ],
                        max_length=16,
                    ),
                ),
                ("reply", models.TextField(blank=True, default="")),
                ("tool_steps", models.JSONField(blank=True, default=list)),
                ("error_code", models.CharField(blank=True, default="", max_length=64)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                (
                    "job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="runs",
                        to="projects.scheduledjob",
                    ),
                ),
            ],
            options={"ordering": ["-started_at"]},
        ),
        migrations.CreateModel(
            name="AgentMessage",
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
                ("from_agent_type", models.CharField(max_length=32)),
                ("to_agent_type", models.CharField(max_length=32)),
                ("subject", models.CharField(blank=True, default="", max_length=300)),
                ("body", models.JSONField(blank=True, default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "pending"), ("consumed", "consumed")],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_messages",
                        to="projects.project",
                    ),
                ),
                (
                    "source_conversation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="agent_messages",
                        to="projects.conversation",
                    ),
                ),
            ],
            options={"ordering": ["created_at"]},
        ),
    ]
