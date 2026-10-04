from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0014_project_growth_hub"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectDebugProfile",
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
                ("last_url", models.CharField(blank=True, default="", max_length=500)),
                ("preferred_categories", models.JSONField(blank=True, default=list)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="debug_profile",
                        to="projects.project",
                    ),
                ),
            ],
            options={
                "verbose_name": "پروفایل دیباگ",
                "verbose_name_plural": "پروفایل‌های دیباگ",
            },
        ),
        migrations.CreateModel(
            name="DebugScan",
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
                ("url", models.CharField(max_length=500)),
                ("categories", models.JSONField(blank=True, default=list)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("running", "running"),
                            ("completed", "completed"),
                            ("failed", "failed"),
                        ],
                        default="running",
                        max_length=16,
                    ),
                ),
                ("findings", models.JSONField(blank=True, default=list)),
                ("metrics", models.JSONField(blank=True, default=dict)),
                ("summary", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="debug_scans",
                        to="projects.project",
                    ),
                ),
            ],
            options={
                "verbose_name": "اسکن دیباگ",
                "verbose_name_plural": "اسکن‌های دیباگ",
                "ordering": ["-created_at"],
            },
        ),
    ]
