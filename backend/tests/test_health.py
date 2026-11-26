"""健康检查接口测试。"""

from unittest.mock import patch

from django.test import TestCase


class HealthCheckTests(TestCase):
    def test_shallow_health(self):
        response = self.client.get('/api/health/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_deep_health_all_components_ok(self):
        with patch('search.client.es_is_available', return_value=True):
            response = self.client.get('/api/health/?deep=1')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(
            data['components'],
            {'database': 'ok', 'cache': 'ok', 'elasticsearch': 'ok'},
        )

    def test_deep_health_reports_elasticsearch_failure(self):
        with patch('search.client.es_is_available', return_value=False):
            response = self.client.get('/api/health/?deep=1')

        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data['status'], 'degraded')
        self.assertEqual(data['components']['elasticsearch'], 'error')
        self.assertEqual(data['components']['database'], 'ok')
