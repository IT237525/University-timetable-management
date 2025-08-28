from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User, Batch


class HealthCheckTests(APITestCase):
    def test_health_ok(self):
        url = reverse('api-health')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get('status'), 'ok')


class WeeklyBatchViewTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='pass', role='admin')
        self.client.force_authenticate(user=self.admin)
        self.batch = Batch.objects.create(
            name='Y1S1',
            description='Test batch',
            academic_year='2024-2025',
            semester='1',
            start_date='2025-01-01',
            end_date='2025-05-15'
        )

    def test_weekly_batch_empty(self):
        url = reverse('weekly-batch') + f'?batch_id={self.batch.id}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('weekly_schedule', resp.data)
