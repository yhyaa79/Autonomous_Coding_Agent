from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0003_expand_agent_types"),
    ]

    operations = [
        migrations.AlterField(
            model_name="conversation",
            name="agent_type",
            field=models.CharField(
                choices=[
                    ("coding", "coding"),
                    ("autonomous", "autonomous"),
                    ("seo", "seo"),
                    ("social", "social"),
                ],
                default="coding",
                max_length=32,
            ),
        ),
    ]
