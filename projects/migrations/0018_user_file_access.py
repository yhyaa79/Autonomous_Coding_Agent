from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0017_sharedtool_tags"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserFileAccess",
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
                    "always_context_paths",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="فایل‌هایی که محتوایشان در هر نوبت به ایجنت تزریق می‌شود (همهٔ پروژه‌ها)",
                    ),
                ),
                (
                    "denied_content_paths",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="فایل‌هایی که ایجنت محتوایشان را نمی‌بیند (همهٔ پروژه‌ها)",
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=models.CASCADE,
                        related_name="file_access",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "دسترسی فایل کاربر",
                "verbose_name_plural": "دسترسی فایل کاربران",
            },
        ),
    ]
