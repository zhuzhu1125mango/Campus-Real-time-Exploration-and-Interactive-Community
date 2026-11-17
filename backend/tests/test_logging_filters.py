"""日志脱敏过滤器测试。"""

import logging

from django.test import SimpleTestCase

from core.logging_filters import SensitiveDataFilter


class SensitiveDataFilterTests(SimpleTestCase):
    """SensitiveDataFilter 的脱敏规则测试。"""

    def _render(self, message, *args):
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg=message,
            args=args,
            exc_info=None,
        )
        SensitiveDataFilter().filter(record)
        return record.getMessage()

    def test_masks_phone_number(self):
        self.assertEqual(
            self._render('用户 13800138000 登录'),
            '用户 138****8000 登录',
        )

    def test_masks_email(self):
        self.assertEqual(
            self._render('邮箱 alice@example.com 已验证'),
            '邮箱 a***@example.com 已验证',
        )

    def test_masks_bearer_token(self):
        self.assertEqual(
            self._render('请求头 Bearer abc.def-123'),
            '请求头 Bearer ***',
        )

    def test_masks_authorization_header(self):
        self.assertEqual(
            self._render('Authorization: Bearer abc.def-123'),
            'authorization=***',
        )

    def test_masks_key_value_tokens(self):
        self.assertEqual(
            self._render('access_token=abcdef123456, password: secret123'),
            'access_token=***, password=***',
        )

    def test_masks_formatted_args(self):
        self.assertEqual(
            self._render('phone=%s email=%s', '13800138000', 'bob@example.com'),
            'phone=138****8000 email=b***@example.com',
        )

    def test_leaves_normal_message_unchanged(self):
        message = '用户 alice 发布了内容'
        self.assertEqual(self._render(message), message)
