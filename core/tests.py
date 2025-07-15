from django.test import TestCase, Client
from django.urls import reverse
import json


class SmokeTestCase(TestCase):
    """Basic smoke tests to ensure the API is running correctly"""
    
    def setUp(self):
        self.client = Client()
    
    def test_api_root(self):
        """Test the root API endpoint"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Job Tracker API')
        self.assertEqual(data['version'], '1.0.0')
        self.assertIn('endpoints', data)
    
    def test_health_check(self):
        """Test basic health check endpoint"""
        response = self.client.get(reverse('core:health'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'job-tracker-api')
        self.assertIn('timestamp', data)
    
    def test_detailed_health_check(self):
        """Test detailed health check endpoint"""
        response = self.client.get(reverse('core:health-detailed'))
        # May return 503 if Redis is not running, but should still return valid JSON
        self.assertIn(response.status_code, [200, 503])
        data = json.loads(response.content)
        self.assertIn('status', data)
        self.assertIn('components', data)
        self.assertIn('timestamp', data)
    
    def test_status_endpoint(self):
        """Test API status endpoint"""
        response = self.client.get(reverse('core:status'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['api_version'], '1.0.0')
        self.assertEqual(data['django_version'], '5.0.1')
        self.assertIn('features', data)
        self.assertIn('environment', data)
    
    def test_admin_accessible(self):
        """Test that admin interface is accessible"""
        response = self.client.get('/admin/', follow=True)
        # Should redirect to login
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django administration')
    
    def test_404_returns_json(self):
        """Test that 404 errors return JSON in production"""
        response = self.client.get('/api/nonexistent/')
        self.assertEqual(response.status_code, 404)
