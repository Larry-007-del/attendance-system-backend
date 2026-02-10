from django.core.management.base import BaseCommand

from attendance.models import BootstrapFlag


class Command(BaseCommand):
    help = "Reset the bootstrap flag for superuser creation."

    def handle(self, *args, **options):
        deleted_count, _ = BootstrapFlag.objects.filter(key="superuser_bootstrap").delete()
        if deleted_count:
            self.stdout.write("Bootstrap flag reset.")
            return

        self.stdout.write("Bootstrap flag not found. Nothing to reset.")
