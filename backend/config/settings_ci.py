"""CI 专用 Django 设置。

仅用于 GitHub Actions / 本地 CI 复现，禁止用于生产或日常开发。

特点：
- 使用内存缓存与内存 Channel Layer，不依赖 Redis。
- Celery 任务同步执行，不依赖 RabbitMQ/Worker。
- 使用快速密码哈希，显著缩短测试时间。
- Elasticsearch 指向不可用地址，验证搜索降级路径。
"""

from .settings import *  # noqa: F401,F403

DEBUG = True

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

ELASTICSEARCH_HOSTS = ['http://127.0.0.1:1']
ELASTICSEARCH_TIMEOUT = 1
ELASTICSEARCH_FALLBACK_TO_DB = True
