import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings

from attendance.models import Course, CourseEnrollment, Lecturer, Student


class Command(BaseCommand):
    help = "Seed minimal sample data for Lecturer, Student, Course, and Enrollment."

    def handle(self, *args, **options):
        if not settings.DEBUG and os.getenv("ALLOW_SEED_DATA", "false").lower() != "true":
            self.stdout.write("Seeding disabled. Set ALLOW_SEED_DATA=true to override.")
            return

        User = get_user_model()

        lecturer_user, lecturer_user_created = User.objects.get_or_create(
            username="lecturer_user",
            defaults={
                "email": "lecturer@example.com",
            },
        )
        if lecturer_user_created:
            lecturer_user.set_password("ChangeMe123!")
            lecturer_user.save(update_fields=["password"])

        student_user, student_user_created = User.objects.get_or_create(
            username="student_user",
            defaults={
                "email": "student@example.com",
            },
        )
        if student_user_created:
            student_user.set_password("ChangeMe123!")
            student_user.save(update_fields=["password"])

        lecturer, _ = Lecturer.objects.get_or_create(
            user=lecturer_user,
            defaults={
                "staff_id": "L0001",
                "name": "Sample Lecturer",
            },
        )

        student, _ = Student.objects.get_or_create(
            user=student_user,
            defaults={
                "student_id": "S0001",
                "name": "Sample Student",
            },
        )

        course, _ = Course.objects.get_or_create(
            course_code="CSC101",
            defaults={
                "name": "Intro to Computing",
                "lecturer": lecturer,
                "latitude": 5.6037,  # Sample coordinates (University of Ghana)
                "longitude": -0.1870,
                "radius_meters": 100.00,
            },
        )

        CourseEnrollment.objects.get_or_create(course=course, student=student)

        self.stdout.write("Seed data ready:")
        self.stdout.write("- Lecturer: lecturer_user / ChangeMe123!")
        self.stdout.write("- Student: student_user / ChangeMe123!")
        self.stdout.write("- Course: CSC101")
