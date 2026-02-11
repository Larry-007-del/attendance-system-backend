from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from geopy.distance import geodesic
from datetime import timedelta
from django.utils import timezone

class Lecturer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='lecturer_pictures/', blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)  # Added field
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.staff_id})"

    def validate_coordinates(self):
        if self.latitude is not None and self.longitude is not None:
            if not (-90 <= self.latitude <= 90 and -180 <= self.longitude <= 180):
                raise ValidationError("Invalid latitude or longitude.")

    def clean(self):
        self.validate_coordinates()
        super().clean()

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='student_pictures/', blank=True, null=True)
    programme_of_study = models.CharField(max_length=255, blank=True, null=True)  # Added field
    year = models.CharField(max_length=2, blank=True, null=True)  # Added field
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.student_id})"

    def get_full_name(self):
        return f"{self.name} ({self.student_id})"

class Course(models.Model):
    name = models.CharField(max_length=100)
    course_code = models.CharField(max_length=10, unique=True)
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='courses')
    students = models.ManyToManyField(Student, through='CourseEnrollment', related_name='courses')
    is_active = models.BooleanField(default=False)
    
    # Geofencing fields
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    radius_meters = models.DecimalField(max_digits=10, decimal_places=2, default=100.00, help_text="Radius in meters for geofencing validation")

    def __str__(self):
        return f"{self.name} ({self.course_code})"

    def clean(self):
        if not Lecturer.objects.filter(id=self.lecturer_id).exists():
            raise ValidationError("Lecturer does not exist.")
        super().clean()

    def has_geofence(self):
        """Check if course has geofencing enabled"""
        return self.latitude is not None and self.longitude is not None

    def validate_location(self, student_latitude, student_longitude, max_distance_meters=None):
        """
        Validate if student is within the geofence radius
        Returns (is_valid, distance_meters) tuple
        """
        if not self.has_geofence():
            return (True, 0.0)  # No geofence, allow all
        
        if student_latitude is None or student_longitude is None:
            return (False, -1.0)  # Student location not provided
        
        try:
            from decimal import Decimal
            course_location = (float(self.latitude), float(self.longitude))
            student_location = (float(student_latitude), float(student_longitude))
            
            distance = geodesic(course_location, student_location).meters
            max_dist = max_distance_meters or float(self.radius_meters)
            
            return (distance <= max_dist, round(distance, 2))
        except Exception as e:
            raise ValidationError(f"Location validation error: {str(e)}")

class CourseEnrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'student')

class Attendance(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateField()
    present_students = models.ManyToManyField(Student, related_name='attended_classes')
    lecturer_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lecturer_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='created_attendances', on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(User, related_name='updated_attendances', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.course.name} - {self.date} (Active: {self.is_active})"

    def save(self, *args, **kwargs):
        if self.is_active:
            self.course.is_active = True
            self.course.save()
        if self.ended_at is not None:
            self.is_active = False
        super().save(*args, **kwargs)


    def is_open(self):
        return self.is_active and (self.ended_at is None or self.ended_at > timezone.now())

class AttendanceToken(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    token = models.CharField(max_length=6, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.course.name} - {self.token}"

    def save(self, *args, **kwargs):
        if self.generated_at is None:
            self.generated_at = timezone.now()

        if self.expires_at is None:
            self.expires_at = self.generated_at + timedelta(hours=4)

        if self.expires_at <= timezone.now():
            self.is_active = False

        super().save(*args, **kwargs)


class BootstrapFlag(models.Model):
    key = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.key


class PendingAttendance(models.Model):
    """Model for storing offline attendance records that need to be synced"""
    student_id = models.CharField(max_length=10)
    course_id = models.IntegerField()
    token = models.CharField(max_length=6)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    timestamp = models.DateTimeField()
    device_id = models.CharField(max_length=100, blank=True, null=True)
    synced = models.BooleanField(default=False)
    synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pending: Student {self.student_id} - Course {self.course_id}"
