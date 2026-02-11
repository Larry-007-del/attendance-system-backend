from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views, admin_views

router = DefaultRouter()
router.register(r'lecturers', views.LecturerViewSet, basename='lecturer')
router.register(r'students', views.StudentViewSet, basename='student')
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'attendances', views.AttendanceViewSet, basename='attendance')
router.register(r'attendance-tokens', views.AttendanceTokenViewSet, basename='attendance-token')

urlpatterns = [
    path('', include(router.urls)),
    
    # Authentication endpoints (primary)
    path('auth/login/', views.MobileLoginView.as_view(), name='mobile_login'),
    path('auth/login/student/', views.StudentLoginView.as_view(), name='student_login'),
    path('auth/login/staff/', views.StaffLoginView.as_view(), name='staff_login'),
    path('auth/logout/', views.LogoutView.as_view(), name='api_logout'),
    
    # Legacy authentication endpoints (for backward compatibility)
    path('login/', views.MobileLoginView.as_view(), name='mobile_login_legacy'),
    path('login/student/', views.StudentLoginView.as_view(), name='student_login_legacy'),
    path('login/staff/', views.StaffLoginView.as_view(), name='staff_login_legacy'),
    
    # User profile endpoint
    path('me/profile/', views.UserProfileView.as_view(), name='user_profile'),
    
    # Student endpoints
    path('student/enrolled_courses/', views.StudentEnrolledCoursesView.as_view(), name='student_enrolled_courses'),
    path('student/attendance/history/', views.StudentAttendanceHistoryView.as_view(), name='student_attendance_history'),
    
    # Lecturer endpoints
    path('lecturers/my-courses/', views.LecturerViewSet.as_view({'get': 'my_courses'}), name='lecturer_my_courses'),
    path('lecturer/attendance/history/', views.LecturerAttendanceHistoryView.as_view(), name='lecturer_attendance_history'),
    
    # Attendance endpoints
    path('courses/take_attendance/', views.CourseViewSet.as_view({'post': 'take_attendance'}), name='take_attendance'),
    path('submit-location/', views.SubmitLocationView.as_view(), name='submit_location'),
    path('attendance/end_attendance/', views.AttendanceViewSet.as_view({'post': 'end_attendance'}), name='end_attendance'),
    path('lecturer-location/', views.LecturerLocationView.as_view(), name='lecturer_location'),
    
    # Legacy endpoints
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    
    # Offline sync endpoints
    path('sync/attendance/', views.SyncAttendanceView.as_view(), name='sync_attendance'),
    path('sync/pending/', views.ProcessPendingAttendanceView.as_view(), name='process_pending'),
    
    # Admin dashboard URLs
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/students/', admin_views.admin_students, name='admin_students'),
    path('admin/lecturers/', admin_views.admin_lecturers, name='admin_lecturers'),
    path('admin/courses/', admin_views.admin_courses, name='admin_courses'),
    path('admin/reports/', admin_views.admin_attendance_report, name='admin_attendance_report'),
    
    # Push notification endpoints
    path('notifications/register/', views.RegisterDeviceView.as_view(), name='register_device'),
    path('notifications/subscribe/<int:course_id>/', views.SubscribeCourseView.as_view(), name='subscribe_course'),
    path('notifications/send/', views.SendNotificationView.as_view(), name='send_notification'),
]
