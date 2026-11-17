"""敏感词过滤模块。

用于公共聊天室等场景的文本脱敏：命中敏感词后替换为 ``***``。
词表默认内置少量中英文示例，可通过 ``settings.SENSITIVE_WORDS`` 追加或覆盖。
"""

import re

from django.conf import settings


DEFAULT_SENSITIVE_WORDS = ['傻逼', '操你妈', 'fuck', 'shit']


def _get_sensitive_words():
    """返回默认词表与配置词表的并集（去重并保持顺序）。"""
    configured = getattr(settings, 'SENSITIVE_WORDS', None) or []
    words = list(DEFAULT_SENSITIVE_WORDS)
    for word in configured:
        if word and word not in words:
            words.append(word)
    return words


def mask_sensitive(text):
    """将文本中的敏感词替换为 ``***``，大小写不敏感。

    对空值（None 或空字符串）直接返回原值。
    """
    if not text:
        return text

    # 长词优先，避免短词先匹配导致长词残留
    words = sorted(_get_sensitive_words(), key=len, reverse=True)
    if not words:
        return text

    pattern = re.compile('|'.join(re.escape(word) for word in words), re.IGNORECASE)
    return pattern.sub('***', text)
