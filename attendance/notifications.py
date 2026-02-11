from django.db import models
from django.contrib.auth.models import User


class DeviceToken(models.Model):
    """Store FCM device tokens for push notifications"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(max_length=20, default='android')  # android, ios
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'token')

    def __str__(self):
        return f"{self.user.username} - {self.device_type}"


class CourseSubscription(models.Model):
    """Track which courses a user wants notifications for"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course_id')

    def __str__(self):
        return f"{self.user.username} - Course {self.course_id}"
