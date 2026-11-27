"""上传文件病毒扫描测试。"""

from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from core.antivirus import VirusScanError, VirusScanUnavailable, scan_stream

User = get_user_model()


class FakeSocket:
    def __init__(self, response=b'stream: OK\0'):
        self.response = response
        self.sent = b''

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def sendall(self, data):
        self.sent += data

    def recv(self, size):
        chunk, self.response = self.response[:size], self.response[size:]
        return chunk


class ScanStreamTests(TestCase):
    @override_settings(ANTIVIRUS_ENABLED=False)
    def test_disabled_skips_scanning(self):
        """未启用时不连接 clamd。"""
        with patch('core.antivirus.socket.create_connection') as connect:
            scan_stream(BytesIO(b'hello'))
        connect.assert_not_called()

    @override_settings(ANTIVIRUS_ENABLED=True, CLAMAV_HOST='clamav', CLAMAV_PORT=3310)
    def test_clean_file_passes(self):
        """clamd 返回 OK 时通过，并按 INSTREAM 协议发送。"""
        fake = FakeSocket()
        with patch('core.antivirus.socket.create_connection', return_value=fake):
            scan_stream(BytesIO(b'hello world'))

        self.assertTrue(fake.sent.startswith(b'zINSTREAM\0'))
        self.assertTrue(fake.sent.endswith(b'\x00\x00\x00\x00'))

    @override_settings(ANTIVIRUS_ENABLED=True)
    def test_virus_detected(self):
        """clamd 返回 FOUND 时抛出 VirusScanError。"""
        fake = FakeSocket(b'stream: Eicar-Test-Signature FOUND\0')
        with patch('core.antivirus.socket.create_connection', return_value=fake):
            with self.assertRaises(VirusScanError):
                scan_stream(BytesIO(b'X5O!P%@AP'))

    @override_settings(ANTIVIRUS_ENABLED=True)
    def test_service_unavailable(self):
        """clamd 不可达时抛出 VirusScanUnavailable。"""
        with patch('core.antivirus.socket.create_connection', side_effect=OSError('refused')):
            with self.assertRaises(VirusScanUnavailable):
                scan_stream(BytesIO(b'hello'))


class UploadScanIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='scanuser', email='scan@example.com', password='pass12345'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    @override_settings(ANTIVIRUS_ENABLED=True)
    def test_content_image_rejects_infected_file(self):
        """富文本图片上传命中病毒时返回 400。"""
        image = SimpleUploadedFile('test.png', b'fake-image-bytes', content_type='image/png')
        with patch('core.antivirus.scan_stream', side_effect=VirusScanError('Eicar')):
            response = self.client.post('/api/content/images/', {'image': image}, format='multipart')

        self.assertEqual(response.status_code, 400)
        self.assertIn('病毒', response.json()['error'])

    @override_settings(ANTIVIRUS_ENABLED=True)
    def test_content_image_allows_clean_file(self):
        """扫描通过时图片上传成功。"""
        image = SimpleUploadedFile('test.png', b'clean-image-bytes', content_type='image/png')
        with patch('core.antivirus.scan_stream', return_value=None):
            response = self.client.post('/api/content/images/', {'image': image}, format='multipart')

        self.assertEqual(response.status_code, 201)
