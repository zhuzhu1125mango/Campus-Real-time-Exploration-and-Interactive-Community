"""OpenAPI 文档路由测试。"""

from django.test import SimpleTestCase
from rest_framework.test import APIClient


class ApiDocTests(SimpleTestCase):
    """验证 schema 与 Swagger/Redoc 页面可访问。"""

    def setUp(self):
        self.client = APIClient()

    def test_schema_endpoint(self):
        response = self.client.get('/api/schema/')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'openapi', response.content.lower())

    def test_swagger_ui(self):
        response = self.client.get('/api/swagger/')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'swagger', response.content.lower())

    def test_redoc(self):
        response = self.client.get('/api/redoc/')

        self.assertEqual(response.status_code, 200)
