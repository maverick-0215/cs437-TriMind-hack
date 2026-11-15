from django.core.management.base import BaseCommand

from lostfound import services


class Command(BaseCommand):
    help = "S35: delete lost reports closed more than 60 days ago, and the photos of those items."

    def handle(self, *args, **options):
        deleted = services.delete_old_closed_reports()
        self.stdout.write(f"Deleted {deleted} closed lost report(s).")
