import time

from django.core.management.base import BaseCommand

from agent.scheduler_service import tick_due_jobs


class Command(BaseCommand):
    help = "Worker پس‌زمینه: jobهای سررسید را اجرا می‌کند (همیشه در حال اجرا نگه دارید)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=float,
            default=15.0,
            help="ثانیه بین هر tick (پیش‌فرض 15)",
        )
        parser.add_argument(
            "--batch",
            type=int,
            default=5,
            help="حداکثر job در هر tick",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="فقط یک بار tick و خروج",
        )

    def handle(self, *args, **options):
        interval = options["interval"]
        batch = options["batch"]
        self.stdout.write(self.style.SUCCESS("Scheduler worker started"))

        while True:
            results = tick_due_jobs(limit=batch)
            if results:
                self.stdout.write(f"tick: {results}")
            if options["once"]:
                break
            time.sleep(interval)
