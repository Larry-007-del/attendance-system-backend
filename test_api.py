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
    print("\n[TEST] Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/api/", timeout=10)
        print_response(response)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Connection error: {e}")
        return False

def test_swagger():
    """Test Swagger documentation"""
    print("\n[TEST] Testing Swagger Docs...")
    try:
        response = requests.get(f"{BASE_URL}/swagger/", timeout=10)
        print_response(response)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Connection error: {e}")
        return False

def test_login():
    """Test JWT login endpoint"""
    print("\n[TEST] Testing JWT Login...")
    try:
        # Test with seed data credentials
        response = requests.post(
            f"{BASE_URL}/api/auth/token/",
            json={"username": "student_user", "password": "ChangeMe123!"},
            timeout=10
        )
        print_response(response)
        if response.status_code == 200:
            data = response.json()
            print(f"\n[SUCCESS] Token received: {data.get('access', '')[:20]}...")
            return True
        return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Connection error: {e}")
        return False

def test_courses_list():
    """Test courses list endpoint"""
    print("\n[TEST] Testing Courses List...")
    try:
        # First get a token
        login_response = requests.post(
            f"{BASE_URL}/api/auth/token/",
            json={"username": "student_user", "password": "ChangeMe123!"},
            timeout=10
        )
        
        if login_response.status_code != 200:
            print("[ERROR] Failed to get token")
            return False
        
        token = login_response.json().get('access')
        
        response = requests.get(
            f"{BASE_URL}/api/courses/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        print_response(response)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Connection error: {e}")
        return False

def test_attendance_history():
    """Test student attendance history endpoint"""
    print("\n[TEST] Testing Attendance History...")
    try:
        # First get a token
        login_response = requests.post(
            f"{BASE_URL}/api/auth/token/",
            json={"username": "student_user", "password": "ChangeMe123!"},
            timeout=10
        )
        
        if login_response.status_code != 200:
            print("[ERROR] Failed to get token")
            return False
        
        token = login_response.json().get('access')
        
        response = requests.get(
            f"{BASE_URL}/api/student/attendance/history/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        print_response(response)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Connection error: {e}")
        return False

def main():
    print("="*60)
    print("Attendance System API Test")
    print("="*60)
    print(f"Base URL: {BASE_URL}\n")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    results.append(("Swagger Docs", test_swagger()))
    results.append(("JWT Login", test_login()))
    results.append(("Courses List", test_courses_list()))
    results.append(("Attendance History", test_attendance_history()))
    
    # Print summary
    print("="*60)
    print("Test Results Summary")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
