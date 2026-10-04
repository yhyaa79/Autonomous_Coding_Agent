from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0016_server_allow_server_wide_paths"),
    ]

    operations = [
        migrations.AddField(
            model_name="sharedtool",
            name="tags",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
