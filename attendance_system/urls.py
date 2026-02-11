from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponseRedirect, JsonResponse
from django.db import connection
import os
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


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
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Swagger and ReDoc paths
    re_path(r'^swagger(?P<format>\.json|\.yaml)
, schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
