from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0013_project_server_connection"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectGrowthHub",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "lifecycle_stage",
                    models.CharField(
                        choices=[
                            ("build", "build"),
                            ("deployed", "deployed"),
                            ("maintain", "maintain"),
                            ("grow", "grow"),
                        ],
                        default="build",
                        max_length=16,
                    ),
                ),
                ("production_url", models.CharField(blank=True, default="", max_length=500)),
                ("launched_at", models.DateTimeField(blank=True, null=True)),
                ("maintenance_tasks", models.JSONField(blank=True, default=list)),
                ("marketing_tasks", models.JSONField(blank=True, default=list)),
                ("channels", models.JSONField(blank=True, default=dict)),
                ("metrics", models.JSONField(blank=True, default=dict)),
                ("last_maintenance_report", models.TextField(blank=True, default="")),
                ("last_marketing_plan", models.TextField(blank=True, default="")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="growth_hub",
                        to="projects.project",
                    ),
                ),
            ],
            options={
                "verbose_name": "هاب نگهداری و رشد",
                "verbose_name_plural": "هاب نگهداری و رشد",
            },
        ),
    ]
