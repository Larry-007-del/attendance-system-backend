# API Testing Guide

## Base URL
- **Local**: `http://localhost:8000`
- **Production**: `https://attendance-system-backend.onrender.com`

## Authentication

### JWT Token Authentication

All API endpoints (except login) require JWT authentication via Bearer token:

```http
Authorization: Bearer <your_jwt_token>
```

### Login

**Endpoint**: `POST /api/auth/token/`

Request:
```json
{
  "username": "student_user",
  "password": "ChangeMe123!"
}
```

Response:
```json
{
  "refresh": "eyJ0eXAi...",
  "access": "eyJ0eXAi..."
}
```

### Refresh Token

**Endpoint**: `POST /api/auth/token/refresh/`

Request:
```json
{
  "refresh": "<your_refresh_token>"
}
```

## Courses

### List All Courses

**Endpoint**: `GET /api/courses/`

### Get Student Enrolled Courses

**Endpoint**: `GET /api/student/enrolled_courses/`

### Take Attendance (with Geofencing)

**Endpoint**: `POST /api/courses/take_attendance/`

Request:
```json
{
  "token": "123456",
  "latitude": 5.6037,
  "longitude": -0.1870
}
```

Response (Success):
```json
{
  "message": "Attendance recorded successfully.",
  "distance": 15.5
}
```

Response (Geofence Error):
```json
{
  "error": "You are outside the allowed radius. You are 150.2m away from the class location."
}
```

### Generate Attendance Token (Lecturer)

**Endpoint**: `POST /api/courses/{course_id}/generate_attendance_token/`

Request:
```json
{
  "token": "123456",
  "latitude": 5.6037,
  "longitude": -0.1870
}
```

## Attendance

### End Attendance Session

**Endpoint**: `POST /api/attendance/end_attendance/`

Request:
```json
{
  "course_id": 1
}
```

### Student Attendance History

**Endpoint**: `GET /api/student/attendance/history/`

## Offline Sync

### Sync Pending Attendance Records

**Endpoint**: `POST /api/sync/attendance/`

Request:
```json
{
  "records": [
    {
      "student_id": "S0001",
      "course_id": 1,
      "token": "123456",
      "latitude": 5.6037,
      "longitude": -0.1870,
      "timestamp": "2024-01-15T10:30:00Z",
      "device_id": "device123"
    }
  ]
}
```

## Admin Portal

### Dashboard

**Endpoint**: `/admin/dashboard/` (HTML page)

### Students Management

**Endpoint**: `/admin/students/` (HTML page)

### Courses Management

**Endpoint**: `/admin/courses/` (HTML page - shows geofence status)

### Attendance Reports

**Endpoint**: `/admin/reports/` (HTML page)

Query Parameters:
- `course_id` - Filter by course
- `date_from` - Filter from date
- `date_to` - Filter to date

## Testing with curl

```bash
# Login and get token
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "student_user", "password": "ChangeMe123!"}'

# Take attendance
curl -X POST http://localhost:8000/api/courses/take_attendance/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{"token": "123456", "latitude": 5.6037, "longitude": -0.1870}'

# Get enrolled courses
curl http://localhost:8000/api/student/enrolled_courses/ \
  -H "Authorization: Bearer <your_token>"
```

## Django Admin

Access at: `/admin/`

Default credentials:
- Username: `admin`
- Password: `ChangeMe123!`
