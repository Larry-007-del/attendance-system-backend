from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponseRedirect, JsonResponse
from django.db import connection
import os
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


def _db_ok():
    try:
        connection.ensure_connection()
        return True
    except Exception:
        return False


def health_view(request):
    db_ok = _db_ok()
    payload = {'status': 'ok', 'db': 'ok'} if db_ok else {'status': 'degraded', 'db': 'error'}
    return JsonResponse(payload, status=200 if db_ok else 503)


def version_view(request):
    commit = os.getenv('RENDER_GIT_COMMIT') or os.getenv('GIT_SHA') or 'unknown'
    return JsonResponse({'version': commit})


class CustomTokenObtainView(APIView):
    """Custom JWT login that returns user info with tokens"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Determine user role
        if hasattr(user, 'lecturer'):
            role = 'lecturer'
            user_id = user.lecturer.id
            staff_id = user.lecturer.staff_id
        elif hasattr(user, 'student'):
            role = 'student'
            user_id = user.student.id
            student_id = user.student.student_id
        else:
            role = 'admin'
            user_id = user.id
            staff_id = None
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'token_type': 'Bearer',
            'user_id': user_id,
            'username': user.username,
            'email': user.email,
            'role': role,
        })


# Swagger and ReDoc schema view
schema_view = get_schema_view(
    openapi.Info(
        title="Attendance System API",
        default_version='v1',
        description="API documentation for the Attendance System",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('health/', health_view),
    path('api/health/', health_view),
    path('version/', version_view),
    path('api/', include('attendance.urls')),
    path('admin/', admin.site.urls),
    path('', lambda request: HttpResponseRedirect('/api/')),  # Redirect root URL to /api/
    
    # JWT Authentication endpoints
    path('api/auth/token/', CustomTokenObtainView.as_view(), name='token_obtain'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Swagger and ReDoc paths
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
