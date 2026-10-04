from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0010_resource_versions"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="always_context_paths",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="project",
            name="denied_content_paths",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
