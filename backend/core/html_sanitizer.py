"""统一的 HTML 富文本清洗模块。

所有用户可输入的富文本/HTML 字段在入库前都应调用 ``sanitize_html``，
防止 XSS 与样式注入。
"""

import bleach


ALLOWED_TAGS = [
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'strike',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'pre', 'code',
    'a', 'img', 'span', 'div', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
]


ALLOWED_ATTRIBUTES = {
    '*': ['class', 'style'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'width', 'height'],
}


ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_html(value: str) -> str:
    """清洗 HTML 富文本，仅保留白名单内的标签与属性。

    对空值（None 或空字符串）直接返回原值，避免无意义转换。
    """
    if not value:
        return value

    return bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
