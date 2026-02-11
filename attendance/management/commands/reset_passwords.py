from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Reset passwords for seed data users"

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Reset lecturer user
        try:
            lecturer = User.objects.get(username='lecturer_user')
            lecturer.set_password('ChangeMe123!')
            lecturer.save()
            self.stdout.write(self.style.SUCCESS(f"Reset password for lecturer_user"))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("lecturer_user does not exist"))
        
        # Reset student user
        try:
            student = User.objects.get(username='student_user')
            student.set_password('ChangeMe123!')
            student.save()
            self.stdout.write(self.style.SUCCESS(f"Reset password for student_user"))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("student_user does not exist"))
