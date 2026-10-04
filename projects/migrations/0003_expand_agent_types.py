from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0002_multi_agent"),
    ]

    operations = [
        migrations.AlterField(
            model_name="conversation",
            name="agent_type",
            field=models.CharField(
                choices=[
                    ("coding", "coding"),
                    ("seo", "seo"),
                    ("scheduler", "scheduler"),
                    ("product", "product"),
                    ("mentor", "mentor"),
                    ("pm", "pm"),
                    ("architect", "architect"),
                    ("qa", "qa"),
                    ("devops", "devops"),
                ],
                default="coding",
                max_length=32,
            ),
        ),
    ]
