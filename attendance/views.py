from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import authenticate, logout
from django.utils import timezone
from django.http import HttpResponse
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
import csv
from openpyxl import Workbook
from django.utils.dateparse import parse_date
from collections import defaultdict

from .models import Lecturer, Student, Course, Attendance, AttendanceToken, PendingAttendance, DeviceToken, CourseSubscription
from .serializers import (
    LecturerSerializer,
    StudentSerializer,
    CourseSerializer,
    AttendanceSerializer,
    AttendanceTokenSerializer,
    LogoutSerializer,
    SubmitLocationSerializer,
    MobileLoginRequestSerializer,
    MobileLoginResponseSerializer,
    StudentLoginRequestSerializer,
    StudentLoginResponseSerializer,
    StaffLoginRequestSerializer,
    StaffLoginResponseSerializer,
    SubmitLocationResponseSerializer,
    AttendanceTokenGenerateRequestSerializer,
    AttendanceTakeRequestSerializer,
    AttendanceTakeResponseSerializer,
    EndAttendanceRequestSerializer,
    EndAttendanceResponseSerializer,
    AttendanceHistoryByCourseSerializer,
)

# Lecturer ViewSet
class LecturerViewSet(viewsets.ModelViewSet):
    queryset = Lecturer.objects.all()
    serializer_class = LecturerSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='my-courses')
    def my_courses(self, request):
        lecturer = get_object_or_404(Lecturer, user=request.user)
        courses = Course.objects.filter(lecturer=lecturer)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

# Student ViewSet
class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

# Course ViewSet
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    @swagger_auto_schema(
        request_body=AttendanceTokenGenerateRequestSerializer,
        responses={200: AttendanceTokenSerializer},
        operation_summary="Generate attendance token",
        operation_description="Generate a token for a course and optionally store lecturer location.",
    )
    def generate_attendance_token(self, request, pk=None):
        course = self.get_object()
        token_value = request.data.get('token')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')

        if not token_value or not latitude or not longitude:
            return Response({'error': 'Token, latitude, and longitude are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create the attendance token
        token = AttendanceToken.objects.create(
            course=course,
            token=token_value,
            generated_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(hours=4),
            is_active=True
        )

        # Optionally update the lecturer's location
        lecturer = course.lecturer
        lecturer.latitude = latitude
        lecturer.longitude = longitude
        lecturer.save()

        serializer = AttendanceTokenSerializer(token)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    @swagger_auto_schema(
        request_body=AttendanceTakeRequestSerializer,
        responses={200: AttendanceTakeResponseSerializer},
        operation_summary="Take attendance",
        operation_description="Record attendance for the authenticated student using a token with geofencing validation.",
    )
    def take_attendance(self, request):
        token_value = request.data.get('token')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')

        if not token_value:
            return Response({'error': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            attendance_token = AttendanceToken.objects.get(token=token_value, is_active=True)
            course = attendance_token.course
            student = get_object_or_404(Student, user=request.user)

            if student not in course.students.all():
                return Response({'error': 'Student is not enrolled in this course.'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate geofencing if course has geofence enabled
            is_valid, distance = course.validate_location(latitude, longitude)
            if not is_valid:
                if distance < 0:
                    return Response({'error': 'Location data required for this course.'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({
                        'error': f'You are outside the allowed radius. You are {distance:.2f}m away from the class location.'
                    }, status=status.HTTP_400_BAD_REQUEST)

            attendance, created = Attendance.objects.get_or_create(
                course=course,
                date=timezone.now().date()
            )
            attendance.present_students.add(student)
            attendance.save()

            return Response({
                'message': 'Attendance recorded successfully.',
                'distance': distance
            }, status=status.HTTP_200_OK)

        except AttendanceToken.DoesNotExist:
            return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
        
# Attendance ViewSet
class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def generate_excel(self, request):
        attendance_id = request.query_params.get('attendance_id')

        if not attendance_id:
            return Response({'error': 'attendance_id parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        attendance = get_object_or_404(Attendance, id=attendance_id)

        # Create an Excel workbook and add a worksheet
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Attendance Report"

        # Add header row
        worksheet.append(['Student ID', 'Student Name', 'Date of Attendance', 'Status'])

        # Collect present students
        present_students = [(student.student_id, student.name) for student in attendance.present_students.all()]

        # Collect missed students
        course_students = list(attendance.course.students.all())
        missed_students = [(student.student_id, student.name) for student in course_students if student not in attendance.present_students.all()]

        # Write present students
        for student_id, student_name in sorted(present_students):
            worksheet.append([student_id, student_name, attendance.date, 'Present'])

        # Write absent students
        for student_id, student_name in sorted(missed_students):
            worksheet.append([student_id, student_name, attendance.date, 'Absent'])

        # Create an HTTP response with the Excel file
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="attendance_{attendance_id}.xlsx"'

        workbook.save(response)
        return response

    @action(detail=False, methods=['post'], url_path='end_attendance')
    @swagger_auto_schema(
        request_body=EndAttendanceRequestSerializer,
        responses={200: EndAttendanceResponseSerializer},
        operation_summary="End attendance session",
        operation_description="Close the active attendance session for a course.",
    )
    def end_attendance(self, request):
        course_id = request.data.get('course_id')
        if not course_id:
            return Response({'error': 'course_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Retrieve the most recent attendance for the course
            attendance = Attendance.objects.filter(course_id=course_id, is_active=True).latest('date')
        except Attendance.DoesNotExist:
            return Response({'error': 'No active attendance found for the course.'}, status=status.HTTP_404_NOT_FOUND)

        attendance.is_active = False
        attendance.ended_at = timezone.now()
        attendance.save()
        return Response({'status': 'Attendance session ended successfully'}, status=status.HTTP_200_OK)
    

# AttendanceToken ViewSet
class AttendanceTokenViewSet(viewsets.ModelViewSet):
    queryset = AttendanceToken.objects.all()
    serializer_class = AttendanceTokenSerializer
    permission_classes = [IsAuthenticated]

# Student Enrolled Courses View
class StudentEnrolledCoursesView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        student = get_object_or_404(Student, user=user)
        return Course.objects.filter(students=student)

# Custom Login Views
class StudentLoginView(ObtainAuthToken):
    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True))
    @swagger_auto_schema(
        request_body=StudentLoginRequestSerializer,
        responses={200: StudentLoginResponseSerializer},
        operation_summary="Student login",
        operation_description="Authenticate a student using username, password, and student_id.",
    )
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        student_id = request.data.get('student_id')

        user = authenticate(request, username=username, password=password)
        if user and hasattr(user, 'student'):
            student = user.student

            if student.student_id == student_id:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user_id': user.student.id,
                    'username': user.username,
                    'student_id': student.student_id
                })
            else:
                return Response({'error': 'Invalid student ID'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

class StaffLoginView(ObtainAuthToken):
    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True))
    @swagger_auto_schema(
        request_body=StaffLoginRequestSerializer,
        responses={200: StaffLoginResponseSerializer},
        operation_summary="Staff login",
        operation_description="Authenticate staff using username, password, and staff_id.",
    )
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        staff_id = request.data.get('staff_id')

        user = authenticate(request, username=username, password=password)
        if user and hasattr(user, 'lecturer'):
            lecturer = user.lecturer
            if lecturer.staff_id == staff_id:
                token, created = Token.objects.get_or_create(user=user)

                return Response({
                    'token': token.key,
                    'user_id': user.lecturer.id,
                    'username': user.username,
                    'staff_id': lecturer.staff_id
                })
            else:
                return Response({'error': 'Invalid staff ID'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


class MobileLoginView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True))
    @swagger_auto_schema(
        request_body=MobileLoginRequestSerializer,
        responses={200: MobileLoginResponseSerializer},
        operation_summary="Mobile login",
        operation_description=(
            "Authenticate a user and return a token. Students must include "
            "student_id; staff must include staff_id."
        ),
    )
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        student_id = request.data.get('student_id')
        staff_id = request.data.get('staff_id')

        if not username or not password:
            return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

        token, _ = Token.objects.get_or_create(user=user)
        payload = {
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
        }

        if hasattr(user, 'student'):
            if not student_id:
                return Response({'error': 'student_id is required for student login.'}, status=status.HTTP_400_BAD_REQUEST)
            if user.student.student_id != student_id:
                return Response({'error': 'Invalid student ID.'}, status=status.HTTP_400_BAD_REQUEST)
            payload.update({
                'role': 'student',
                'student_id': user.student.student_id,
            })
        elif hasattr(user, 'lecturer'):
            if not staff_id:
                return Response({'error': 'staff_id is required for staff login.'}, status=status.HTTP_400_BAD_REQUEST)
            if user.lecturer.staff_id != staff_id:
                return Response({'error': 'Invalid staff ID.'}, status=status.HTTP_400_BAD_REQUEST)
            payload.update({
                'role': 'staff',
                'staff_id': user.lecturer.staff_id,
            })
        else:
            payload['role'] = 'user'

        return Response(payload)

# Logout View
class LogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        request.user.auth_token.delete()
        logout(request)
        return Response(status=status.HTTP_200_OK)

# Location-based Attendance View
class SubmitLocationView(generics.GenericAPIView):
    serializer_class = SubmitLocationSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=SubmitLocationSerializer,
        responses={200: SubmitLocationResponseSerializer},
        operation_summary="Submit attendance location",
        operation_description=(
            "Validate a student's location against an active attendance token "
            "and mark attendance if within the allowed radius."
        ),
    )
    def post(self, request, *args, **kwargs):
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        attendance_token = request.data.get('attendance_token')

        try:
            token = AttendanceToken.objects.get(token=attendance_token, is_active=True)
        except AttendanceToken.DoesNotExist:
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        attendance = Attendance.objects.filter(course=token.course, date=timezone.now().date()).first()

        if attendance and attendance.is_within_radius(float(latitude), float(longitude)):
            user = request.user
            if hasattr(user, 'student'):
                student = user.student
                if student in token.course.students.all():
                    attendance.present_students.add(student)
                    attendance.save()
                    return Response({'status': 'Attendance marked successfully'}, status=status.HTTP_200_OK)
            return Response({'error': 'Student not enrolled in this course'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Location is out of range'}, status=status.HTTP_400_BAD_REQUEST)

# Student Attendance History View
from rest_framework.response import Response

class StudentAttendanceHistoryView(generics.GenericAPIView):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: AttendanceHistoryByCourseSerializer(many=True)},
        operation_summary="Student attendance history",
        operation_description="Return a student's attendance history grouped by course.",
    )
    def get(self, request, *args, **kwargs):
        # Fetch the current user and the corresponding student object
        user = self.request.user
        student = get_object_or_404(Student, user=user)

        # Retrieve attendance records where the student was present
        attendance_records = Attendance.objects.filter(
            present_students=student
        ).order_by('-date')

        # Categorize records by course code and order by date descending within each course
        categorized_records = defaultdict(list)
        for attendance in attendance_records:
            course_code = attendance.course.course_code
            categorized_records[course_code].append({
                'date': attendance.date.strftime('%Y-%m-%d'),
            })

        # Prepare the response data
        response_data = [{'course_code': course, 'attendances': records} for course, records in categorized_records.items()]

        return Response(response_data)
    
#Lecturer Attendance History View
class LecturerAttendanceHistoryView(generics.GenericAPIView):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: AttendanceHistoryByCourseSerializer(many=True)},
        operation_summary="Lecturer attendance history",
        operation_description="Return attendance history for courses taught by the lecturer.",
    )
    def get(self, request, *args, **kwargs):
        # Fetch the current user and the corresponding lecturer object
        user = self.request.user
        lecturer = get_object_or_404(Lecturer, user=user)

        # Retrieve attendance records for courses taught by the lecturer
        attendance_records = Attendance.objects.filter(
            course__lecturer=lecturer
        ).order_by('-date')

        # Categorize records by course code and order by date descending within each course
        categorized_records = defaultdict(list)
        for attendance in attendance_records:
            course_code = attendance.course.course_code
            categorized_records[course_code].append({
                'date': attendance.date.strftime('%Y-%m-%d'),
            })

        # Prepare the response data
        response_data = [{'course_code': course, 'attendances': records} for course, records in categorized_records.items()]

        return Response(response_data)
# Lecturer Location View
class LecturerLocationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        token_value = request.data.get('token')

        try:
            token = AttendanceToken.objects.get(token=token_value, is_active=True)
            lecturer = token.course.lecturer

            if lecturer.latitude is None or lecturer.longitude is None:
                return Response({'error': 'Lecturer coordinates not set.'}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'longitude': lecturer.longitude,
                'latitude': lecturer.latitude,
                'token': token.token
            }, status=status.HTTP_200_OK)

        except AttendanceToken.DoesNotExist:
            return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)


# User Profile View
class UserProfileView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Get the current user's profile information"""
        user = request.user
        
        profile_data = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        
        # Add role-specific data
        if hasattr(user, 'student'):
            student = user.student
            profile_data.update({
                'role': 'student',
                'student_id': student.student_id,
                'name': student.name,
                'programme_of_study': student.programme_of_study,
                'year': student.year,
                'phone_number': student.phone_number,
            })
        elif hasattr(user, 'lecturer'):
            lecturer = user.lecturer
            profile_data.update({
                'role': 'staff',
                'staff_id': lecturer.staff_id,
                'name': lecturer.name,
                'department': lecturer.department,
                'phone_number': lecturer.phone_number,
            })
        else:
            profile_data['role'] = 'user'
        
        return Response(profile_data)


# Offline Sync Views
class SyncAttendanceView(APIView):
    """
    API endpoint for syncing offline attendance records.
    
    Mobile app sends batch of attendance records that were recorded offline.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'records': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'student_id': openapi.Schema(type=openapi.TYPE_STRING),
                            'course_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'token': openapi.Schema(type=openapi.TYPE_STRING),
                            'latitude': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'longitude': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'timestamp': openapi.Schema(type=openapi.TYPE_STRING, description='ISO 8601 datetime'),
                            'device_id': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    ),
                    description='List of attendance records to sync'
                )
            }
        ),
        responses={
            200: openapi.Schema(type=openapi.TYPE_OBJECT),
            400: openapi.Schema(type=openapi.TYPE_OBJECT),
        },
        operation_summary="Sync offline attendance records",
        operation_description="Submit batch of attendance records recorded while offline"
    )
    def post(self, request):
        records = request.data.get('records', [])
        
        if not records:
            return Response({'error': 'No records provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        synced_count = 0
        pending_count = 0
        errors = []
        
        for record in records:
            try:
                student_id = record.get('student_id')
                course_id = record.get('course_id')
                token_value = record.get('token')
                latitude = record.get('latitude')
                longitude = record.get('longitude')
                timestamp = record.get('timestamp')
                device_id = record.get('device_id')
                
                # Check if this is a duplicate
                existing = PendingAttendance.objects.filter(
                    student_id=student_id,
                    course_id=course_id,
                    token=token_value,
                    timestamp__minute__range=[
                        timezone.now().replace(second=0, microsecond=0).minute - 1,
                        timezone.now().replace(second=0, microsecond=0).minute + 1
                    ]
                ).exists()
                
                if existing:
                    continue
                
                # Try to process immediately if token is valid
                try:
                    attendance_token = AttendanceToken.objects.get(
                        token=token_value,
                        course_id=course_id,
                        is_active=True
                    )
                    
                    student = Student.objects.get(student_id=student_id)
                    attendance = Attendance.objects.get(
                        course_id=course_id,
                        is_active=True
                    )
                    
                    attendance.present_students.add(student)
                    synced_count += 1
                    
                except (AttendanceToken.DoesNotExist, Student.DoesNotExist, Attendance.DoesNotExist):
                    # Store as pending for later processing
                    PendingAttendance.objects.create(
                        student_id=student_id,
                        course_id=course_id,
                        token=token_value,
                        latitude=latitude,
                        longitude=longitude,
                        timestamp=timestamp,
                        device_id=device_id,
                        synced=False
                    )
                    pending_count += 1
                    
            except Exception as e:
                errors.append({'record': record, 'error': str(e)})
        
        return Response({
            'synced': synced_count,
            'pending': pending_count,
            'total': len(records),
            'errors': errors if errors else None
        })


class ProcessPendingAttendanceView(APIView):
    """
    Process pending attendance records.
    Admin endpoint to process records stored when device was offline.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get pending attendance records"""
        pending = PendingAttendance.objects.filter(synced=False).order_by('-timestamp')
        
        data = [{
            'id': p.id,
            'student_id': p.student_id,
            'course_id': p.course_id,
            'token': p.token,
            'timestamp': p.timestamp,
            'created_at': p.created_at
        } for p in pending]
        
        return Response({'pending_records': data, 'count': len(data)})
    
    def post(self, request):
        """Process all pending records"""
        pending = PendingAttendance.objects.filter(synced=False)
        
        processed = 0
        failed = 0
        
        for record in pending:
            try:
                attendance_token = AttendanceToken.objects.get(
                    token=record.token,
                    course_id=record.course_id,
                    is_active=True
                )
                
                student = Student.objects.get(student_id=record.student_id)
                attendance = Attendance.objects.get(
                    course_id=record.course_id,
                    is_active=True
                )
                
                attendance.present_students.add(student)
                record.synced = True
                record.synced_at = timezone.now()
                record.save()
                processed += 1
                
            except Exception as e:
                failed += 1
        
        return Response({
            'processed': processed,
            'failed': failed,
            'total': processed + failed
        })


# Push Notification Views
class RegisterDeviceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        fcm_token = request.data.get('fcm_token')
        device_type = request.data.get('device_type', 'android')
        
        if not fcm_token:
            return Response({'error': 'FCM token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        DeviceToken.objects.update_or_create(
            user=request.user,
            token=fcm_token,
            defaults={'device_type': device_type}
        )
        
        return Response({'message': 'Device token registered successfully'})


class SubscribeCourseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        CourseSubscription.objects.get_or_create(
            user=request.user,
            course_id=course_id
        )
        return Response({'message': 'Subscribed to course notifications'})

    def delete(self, request, course_id):
        CourseSubscription.objects.filter(
            user=request.user,
            course_id=course_id
        ).delete()
        return Response({'message': 'Unsubscribed from course notifications'})


class SendNotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Send notification to subscribed users (for lecturers)"""
        title = request.data.get('title')
        body = request.data.get('body')
        course_id = request.data.get('course_id')
        
        if not title or not body:
            return Response({'error': 'Title and body are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get subscribed users
        if course_id:
            subscriptions = CourseSubscription.objects.filter(course_id=course_id)
        else:
            subscriptions = CourseSubscription.objects.all()
        
        # Get device tokens for subscribed users
        user_ids = subscriptions.values_list('user_id', flat=True)
        tokens = DeviceToken.objects.filter(user_id__in=user_ids).values_list('token', flat=True)
        
        # Send notifications (using Firebase HTTP API - requires server key)
        # For demo purposes, we'll just log this
        print(f'Would send notification to {len(tokens)} devices')
        print(f'Title: {title}, Body: {body}')
        
        return Response({
            'message': 'Notifications queued',
            'recipients': len(tokens)
        })
