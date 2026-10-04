# Generated manually for conversation feed persistence

from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0008_agent_project_store"),
    ]

    operations = [
        migrations.AddField(
            model_name="conversation",
            name="topic_summary",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="conversation",
            name="total_credits_used",
            field=models.DecimalField(
                decimal_places=6,
                default=Decimal("0"),
                max_digits=18,
            ),
        ),
        migrations.AddField(
            model_name="conversation",
            name="tool_trace",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.CreateModel(
            name="ConversationFeedItem",
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
                ("turn_index", models.PositiveIntegerField(db_index=True)),
                ("sub_order", models.PositiveIntegerField(default=0)),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("phase_log", "phase_log"),
                            ("tool_step", "tool_step"),
                            ("credits", "credits"),
                            ("thinking", "thinking"),
                        ],
                        max_length=32,
                    ),
                ),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "conversation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="feed_items",
                        to="projects.conversation",
                    ),
                ),
            ],
            options={
                "ordering": ["turn_index", "sub_order", "id"],
            },
        ),
    ]
