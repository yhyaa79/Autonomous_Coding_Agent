from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0012_user_llm_settings"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectServerConnection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_enabled", models.BooleanField(default=False)),
                ("host", models.CharField(blank=True, default="", max_length=255)),
                ("port", models.PositiveIntegerField(default=22)),
                ("username", models.CharField(blank=True, default="", max_length=128)),
                (
                    "auth_method",
                    models.CharField(
                        choices=[("password", "password"), ("private_key", "private_key")],
                        default="password",
                        max_length=16,
                    ),
                ),
                ("secret_encrypted", models.TextField(blank=True, default="")),
                ("key_passphrase_encrypted", models.TextField(blank=True, default="")),
                ("remote_root_path", models.TextField(blank=True, default="")),
                ("strict_host_key", models.BooleanField(default=True)),
                ("host_key_fingerprint", models.CharField(blank=True, default="", max_length=128)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="server_connection",
                        to="projects.project",
                    ),
                ),
            ],
            options={
                "verbose_name": "اتصال SSH پروژه",
                "verbose_name_plural": "اتصال SSH پروژه",
            },
        ),
    ]
