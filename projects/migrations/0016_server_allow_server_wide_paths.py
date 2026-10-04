from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0015_debug_hub"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectserverconnection",
            name="allow_server_wide_paths",
            field=models.BooleanField(default=False),
        ),
    ]
