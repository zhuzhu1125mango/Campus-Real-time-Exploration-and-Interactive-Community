"""对象存储（S3 兼容）配置辅助。

阿里云 OSS、腾讯云 COS、MinIO 均提供 S3 兼容接口，
统一通过 ``django-storages`` 的 S3Storage 接入，避免为每家云厂商单独适配。

启用方式（.env）::

    STORAGE_BACKEND=s3
    STORAGE_S3_BUCKET_NAME=your-bucket
    STORAGE_S3_ENDPOINT_URL=https://oss-cn-hangzhou.aliyuncs.com
    STORAGE_S3_REGION_NAME=oss-cn-hangzhou
    STORAGE_S3_ACCESS_KEY_ID=...
    STORAGE_S3_SECRET_ACCESS_KEY=...
"""

import os

OBJECT_STORAGE_BACKENDS = ('s3', 'oss', 'cos')


def object_storage_enabled(env=None):
    """当前是否启用对象存储。"""
    env = os.environ if env is None else env
    return (env.get('STORAGE_BACKEND') or 'local').strip().lower() in OBJECT_STORAGE_BACKENDS


def build_s3_options(env=None):
    """从环境变量构建 S3Storage 选项，过滤空值。"""
    env = os.environ if env is None else env

    def get(name, default=''):
        return (env.get(name) or default).strip()

    options = {
        'bucket_name': get('STORAGE_S3_BUCKET_NAME'),
        'access_key': get('STORAGE_S3_ACCESS_KEY_ID'),
        'secret_key': get('STORAGE_S3_SECRET_ACCESS_KEY'),
        'endpoint_url': get('STORAGE_S3_ENDPOINT_URL'),
        'region_name': get('STORAGE_S3_REGION_NAME'),
        'location': get('STORAGE_S3_LOCATION'),
        'custom_domain': get('STORAGE_S3_CUSTOM_DOMAIN'),
        'addressing_style': get('STORAGE_S3_ADDRESSING_STYLE', 'virtual'),
        'default_acl': get('STORAGE_S3_DEFAULT_ACL', 'public-read'),
        'querystring_expire': int(get('STORAGE_S3_QUERYSTRING_EXPIRE', '3600')),
        'file_overwrite': False,
    }
    return {key: value for key, value in options.items() if value not in ('', None)}
