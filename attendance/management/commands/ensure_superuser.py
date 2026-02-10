from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
import os

from attendance.models import BootstrapFlag


class Command(BaseCommand):
    help = "Create a superuser from environment variables if it does not exist."

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
        reset_flag = os.getenv("RESET_BOOTSTRAP_FLAG", "false").lower() == "true"

        if not username or not email or not password:
            self.stdout.write("Superuser env vars not set. Skipping.")
            return

        if reset_flag:
            BootstrapFlag.objects.filter(key="superuser_bootstrap").delete()

        if BootstrapFlag.objects.filter(key="superuser_bootstrap").exists():
            self.stdout.write("Superuser bootstrap already completed. Skipping.")
            return

        User = get_user_model()
        existing_user = User.objects.filter(username=username).first()
        if existing_user:
            existing_user.email = email
            existing_user.set_password(password)
            existing_user.is_staff = True
            existing_user.is_superuser = True
            existing_user.save(update_fields=[
                "email",
                "password",
                "is_staff",
                "is_superuser",
            ])
            self.stdout.write("Superuser updated.")
            BootstrapFlag.objects.create(key="superuser_bootstrap")
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        BootstrapFlag.objects.create(key="superuser_bootstrap")
        self.stdout.write("Superuser created.")
