from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Course, Student, Lecturer, Attendance, AttendanceToken

def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard with overview statistics"""
    
    # Get statistics
    total_students = Student.objects.count()
    total_lecturers = Lecturer.objects.count()
    total_courses = Course.objects.count()
    
    # Today's attendance
    today = timezone.now().date()
    today_attendance = Attendance.objects.filter(date=today)
    total_attendance_sessions = today_attendance.count()
    
    # Active attendance sessions
    active_sessions = Attendance.objects.filter(is_active=True).count()
    
    # Active tokens
    active_tokens = AttendanceToken.objects.filter(is_active=True).count()
    
    # Recent activity (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_attendance = Attendance.objects.filter(created_at__gte=week_ago).count()
    
    context = {
        'total_students': total_students,
        'total_lecturers': total_lecturers,
        'total_courses': total_courses,
        'total_attendance_sessions': total_attendance_sessions,
        'active_sessions': active_sessions,
        'active_tokens': active_tokens,
        'recent_attendance': recent_attendance,
    }
    
    return render(request, 'attendance/admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_students(request):
    """List all students with enrollment status"""
    students = Student.objects.all().select_related('user')
    return render(request, 'attendance/admin_students.html', {'students': students})

@login_required
@user_passes_test(is_admin)
def admin_lecturers(request):
    """List all lecturers with their courses"""
    lecturers = Lecturer.objects.all().prefetch_related('courses')
    return render(request, 'attendance/admin_lecturers.html', {'lecturers': lecturers})

@login_required
@user_passes_test(is_admin)
def admin_courses(request):
    """List all courses with geofence status"""
    courses = Course.objects.all().select_related('lecturer')
    
    # Add geofence status to each course
    for course in courses:
        course.has_geofence = course.has_geofence()
    
    return render(request, 'attendance/admin_courses.html', {'courses': courses})

@login_required
@user_passes_test(is_admin)
def admin_attendance_report(request):
    """Generate attendance reports"""
    courses = Course.objects.all()
    
    course_id = request.GET.get('course_id')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    attendances = Attendance.objects.all().select_related('course').prefetch_related('present_students')
    
    if course_id:
        attendances = attendances.filter(course_id=course_id)
    if date_from:
        attendances = attendances.filter(date__gte=date_from)
    if date_to:
        attendances = attendances.filter(date__lte=date_to)
    
    # Calculate attendance rates
    for attendance in attendances:
        total_enrolled = attendance.course.students.count()
        present_count = attendance.present_students.count()
        attendance.attendance_rate = (present_count / total_enrolled * 100) if total_enrolled > 0 else 0
    
    context = {
        'courses': courses,
        'attendances': attendances.order_by('-date'),
    }
    
    return render(request, 'attendance/admin_attendance_report.html', context)
