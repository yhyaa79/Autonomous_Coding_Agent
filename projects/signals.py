from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import MessageBackup


@receiver(post_delete, sender=MessageBackup)
def cleanup_message_backup_files(sender, instance: MessageBackup, **kwargs) -> None:
    from pathlib import Path

    from agent.message_backup import remove_backup_tree

    root = None
    try:
        if instance.project_id and instance.project.root_path:
            root = Path(instance.project.root_path)
    except Exception:
        root = None
    remove_backup_tree(instance.token, root)
