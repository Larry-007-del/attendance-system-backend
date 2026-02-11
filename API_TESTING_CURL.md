# API Testing with cURL

## Base URL
```bash
BASE_URL="https://attendance-system-backend-z1wl.onrender.com"
```

## 1. Health Check
```bash
curl -X GET "$BASE_URL/api/"
```

## 2. Login (Get JWT Token)
```bash
# Student Login
curl -X POST "$BASE_URL/api/auth/token/" \
  -H "Content-Type: application/json" \
  -d '{"username": "student_user", "password": "ChangeMe123!", "student_id": "S0001"}'

# Save the access token
STUDENT_TOKEN="<paste_access_token_here>"

# Lecturer Login
curl -X POST "$BASE_URL/api/auth/token/" \
  -H "Content-Type: application/json" \
  -d '{"username": "lecturer_user", "password": "ChangeMe123!", "staff_id": "L0001"}'

# Save the access token
LECTURER_TOKEN="<paste_access_token_here>"
```

## 3. Get Courses
```bash
curl -X GET "$BASE_URL/api/courses/" \
  -H "Authorization: Bearer $STUDENT_TOKEN"
```

## 4. Get Student Enrolled Courses
```bash
curl -X GET "$BASE_URL/api/student/enrolled_courses/" \
  -H "Authorization: Bearer $STUDENT_TOKEN"
```

## 5. Get Lecturer Courses
```bash
curl -X GET "$BASE_URL/api/lecturers/my-courses/" \
  -H "Authorization: Bearer $LECTURER_TOKEN"
```

## 6. Get User Profile
```bash
curl -X GET "$BASE_URL/api/me/profile/" \
  -H "Authorization: Bearer $STUDENT_TOKEN"
```

## 7. Get Student Attendance History
```bash
curl -X GET "$BASE_URL/api/student/attendance/history/" \
  -H "Authorization: Bearer $STUDENT_TOKEN"
```

## 8. Get Lecturer Attendance History
```bash
curl -X GET "$BASE_URL/api/lecturer/attendance/history/" \
  -H "Authorization: Bearer $LECTURER_TOKEN"
```

## 9. Generate Attendance Token (Lecturer)
```bash
curl -X POST "$BASE_URL/api/courses/1/generate_attendance_token/" \
  -H "Authorization: Bearer $LECTURER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token": "123456", "latitude": 5.6037, "longitude": -0.1870}'
```

## 10. Take Attendance (Student)
```bash
curl -X POST "$BASE_URL/api/courses/take_attendance/" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token": "123456", "latitude": 5.6037, "longitude": -0.1870}'
```

## 11. End Attendance (Lecturer)
```bash
curl -X POST "$BASE_URL/api/attendance/end_attendance/" \
  -H "Authorization: Bearer $LECTURER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"course_id": 1}'
```

## 12. Refresh Token
```bash
curl -X POST "$BASE_URL/api/auth/token/refresh/" \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<your_refresh_token>"}'
```

## Admin Endpoints (HTML Pages)
- Dashboard: `$BASE_URL/admin/dashboard/`
- Students: `$BASE_URL/admin/students/`
- Lecturers: `$BASE_URL/admin/lecturers/`
- Courses: `$BASE_URL/admin/courses/`
- Reports: `$BASE_URL/admin/reports/`

## Django Admin
- Admin Panel: `$BASE_URL/admin/`
