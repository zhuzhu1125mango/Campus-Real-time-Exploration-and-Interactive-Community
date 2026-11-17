"""日志脱敏过滤器。

在日志进入 Handler 前统一屏蔽 token、手机号与邮箱，
避免敏感信息通过控制台或日志文件泄露。
"""

import logging
import re

_BEARER_RE = re.compile(r'(?i)\bBearer\s+[A-Za-z0-9\-_.]+')
_AUTH_HEADER_RE = re.compile(r'(?i)\bauthorization\s*[=:]\s*(?:bearer\s+)?\S+')
_TOKEN_RE = re.compile(
    r'(?i)\b(access_token|refresh_token|token|password|secret)\b'
    r'\s*[=:]\s*["\']?([A-Za-z0-9\-_.]{6,})'
)
_PHONE_RE = re.compile(r'(?<!\d)(1[3-9]\d)(\d{4})(\d{4})(?!\d)')
_EMAIL_RE = re.compile(
    r'([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})'
)


class SensitiveDataFilter(logging.Filter):
    """对日志消息做正则脱敏。"""

    def filter(self, record):
        try:
            message = record.getMessage()
        except Exception:
            return True

        masked = self.mask(message)
        if masked != message:
            record.msg = masked
            record.args = ()
        return True

    @staticmethod
    def mask(text):
        """返回脱敏后的文本。"""
        text = _AUTH_HEADER_RE.sub('authorization=***', text)
        text = _BEARER_RE.sub('Bearer ***', text)
        text = _TOKEN_RE.sub(lambda match: f'{match.group(1)}=***', text)
        text = _PHONE_RE.sub(r'\1****\3', text)
        text = _EMAIL_RE.sub(r'\1***\2', text)
        return text
