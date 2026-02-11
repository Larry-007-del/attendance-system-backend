"""
API Testing Script for Attendance System
Run with: python test_api.py

Note: Replace BASE_URL with your actual backend URL
"""

import requests
import json
import sys

BASE_URL = "https://attendance-system-backend-z1wl.onrender.com"

def print_response(response):
    """Print formatted API response"""
    print(f"\n{'='*60}")
    print(f"Status: {response.status_code}")
    print(f"URL: {response.url}")
    print(f"Response:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print(f"{'='*60}\n")

def test_health_check():
    """Test health endpoint"""
    print("\n🔍 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/api/", timeout=10)
        print_response(response)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def test_swagger():
    """Test Swagger documentation"""
    print("\n📚 Testing Swagger Docs...")
    try:
        response = requests.get(f"{BASE_URL}/swagger/", timeout=10)
        print_response(response)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def test_login():
    """Test JWT login endpoint"""
    print("\n🔐 Testing JWT Login...")
    
    # Test student login
    credentials = [
        {"username": "student_user", "password": "ChangeMe123!", "student_id": "S0001"},
        {"username": "lecturer_user", "password": "ChangeMe123!", "staff_id": "L0001"},
    ]
    
    for creds in credentials:
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/token/",
                json=creds,
                timeout=10
            )
            print(f"Login as {creds['username']}:")
            print_response(response)
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access'), token_data.get('refresh')
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
    
    return None, None

def test_protected_endpoints(token):
    """Test protected endpoints with JWT token"""
    if not token:
        print("❌ No token available for protected endpoints")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test get courses
    print("\n📚 Testing GET /api/courses/")
    try:
        response = requests.get(f"{BASE_URL}/api/courses/", headers=headers, timeout=10)
        print_response(response)
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
    
    # Test student enrolled courses
    print("\n🎓 Testing GET /api/student/enrolled_courses/")
    try:
        response = requests.get(f"{BASE_URL}/api/student/enrolled_courses/", headers=headers, timeout=10)
        print_response(response)
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
    
    # Test lecturer courses
    print("\n👨‍🏫 Testing GET /api/lecturers/my-courses/")
    try:
        response = requests.get(f"{BASE_URL}/api/lecturers/my-courses/", headers=headers, timeout=10)
        print_response(response)
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
    
    # Test user profile
    print("\n👤 Testing GET /api/me/profile/")
    try:
        response = requests.get(f"{BASE_URL}/api/me/profile/", headers=headers, timeout=10)
        print_response(response)
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
    
    # Test student attendance history
    print("\n📊 Testing GET /api/student/attendance/history/")
    try:
        response = requests.get(f"{BASE_URL}/api/student/attendance/history/", headers=headers, timeout=10)
        print_response(response)
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")

def test_token_refresh(refresh_token):
    """Test token refresh"""
    if not refresh_token:
        print("❌ No refresh token available")
        return
    
    print("\n🔄 Testing Token Refresh...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/token/refresh/",
            json={"refresh": refresh_token},
            timeout=10
        )
        print_response(response)
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")

def test_admin_endpoints():
    """Test admin dashboard endpoints"""
    print("\n👨‍💼 Testing Admin Dashboard...")
    
    endpoints = [
        "/admin/dashboard/",
        "/admin/students/",
        "/admin/lecturers/",
        "/admin/courses/",
        "/admin/reports/",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            print(f"{endpoint}: Status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error for {endpoint}: {e}")

def test_django_admin():
    """Test Django admin"""
    print("\n⚙️ Testing Django Admin...")
    try:
        response = requests.get(f"{BASE_URL}/admin/", timeout=10)
        print(f"Django Admin: Status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")

def main():
    print("="*60)
    print("Attendance System API Test")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    
    # Test endpoints
    health_ok = test_health_check()
    
    if health_ok:
        test_swagger()
        access_token, refresh_token = test_login()
        test_protected_endpoints(access_token)
        test_token_refresh(refresh_token)
        test_admin_endpoints()
        test_django_admin()
    else:
        print("\n❌ Backend is not accessible. Please check:")
        print("1. Render deployment is complete")
        print("2. ALLOW_SEED_DATA=true is set")
        print("3. Database migrations have run")
    
    print("\n" + "="*60)
    print("API Testing Complete!")
    print("="*60)

if __name__ == "__main__":
    # Allow overriding base URL from command line
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
    main()
