from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from attendance.models import Lecturer, Student


class HealthVersionTests(APITestCase):
	def test_health_endpoint(self):
		response = self.client.get('/health/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json().get('status'), 'ok')

	def test_version_endpoint(self):
		response = self.client.get('/version/')
		self.assertEqual(response.status_code, 200)
		self.assertIn('version', response.json())


class MobileLoginTests(APITestCase):
	def setUp(self):
		self.student_user = User.objects.create(username='student_user_test', email='student@test.com')
		self.student_user.set_password('ChangeMe123!')
		self.student_user.save(update_fields=['password'])
		Student.objects.create(user=self.student_user, student_id='S1001', name='Student Test')

		self.staff_user = User.objects.create(username='staff_user_test', email='staff@test.com')
		self.staff_user.set_password('ChangeMe123!')
		self.staff_user.save(update_fields=['password'])
		Lecturer.objects.create(user=self.staff_user, staff_id='L1001', name='Staff Test')

	def test_mobile_login_student_requires_id(self):
		response = self.client.post('/api/login/', {
			'username': 'student_user_test',
			'password': 'ChangeMe123!'
		}, format='json')
		self.assertEqual(response.status_code, 400)

	def test_mobile_login_student_success(self):
		response = self.client.post('/api/login/', {
			'username': 'student_user_test',
			'password': 'ChangeMe123!',
			'student_id': 'S1001'
		}, format='json')
		self.assertEqual(response.status_code, 200)
		body = response.json()
		self.assertEqual(body.get('role'), 'student')
		self.assertIn('token', body)

	def test_mobile_login_staff_success(self):
		response = self.client.post('/api/login/', {
			'username': 'staff_user_test',
			'password': 'ChangeMe123!',
			'staff_id': 'L1001'
		}, format='json')
		self.assertEqual(response.status_code, 200)
		body = response.json()
		self.assertEqual(body.get('role'), 'staff')
		self.assertIn('token', body)
