"""对象存储配置辅助测试。"""

from django.test import SimpleTestCase

from core.storage import build_s3_options, object_storage_enabled


class ObjectStorageConfigTests(SimpleTestCase):
    def test_disabled_by_default(self):
        """未配置或 local 时不启用对象存储。"""
        self.assertFalse(object_storage_enabled({}))
        self.assertFalse(object_storage_enabled({'STORAGE_BACKEND': 'local'}))

    def test_enabled_for_s3_compatible_backends(self):
        """s3/oss/cos 均视为对象存储。"""
        for backend in ('s3', 'oss', 'cos', 'S3'):
            self.assertTrue(object_storage_enabled({'STORAGE_BACKEND': backend}))

    def test_build_options_maps_env(self):
        """环境变量应完整映射为 S3Storage 选项。"""
        options = build_s3_options({
            'STORAGE_S3_BUCKET_NAME': 'campus-media',
            'STORAGE_S3_ENDPOINT_URL': 'https://oss-cn-hangzhou.aliyuncs.com',
            'STORAGE_S3_REGION_NAME': 'oss-cn-hangzhou',
            'STORAGE_S3_ACCESS_KEY_ID': 'key-id',
            'STORAGE_S3_SECRET_ACCESS_KEY': 'key-secret',
            'STORAGE_S3_LOCATION': 'media',
            'STORAGE_S3_CUSTOM_DOMAIN': 'cdn.example.com',
            'STORAGE_S3_ADDRESSING_STYLE': 'virtual',
            'STORAGE_S3_DEFAULT_ACL': 'private',
            'STORAGE_S3_QUERYSTRING_EXPIRE': '600',
        })

        self.assertEqual(options['bucket_name'], 'campus-media')
        self.assertEqual(options['endpoint_url'], 'https://oss-cn-hangzhou.aliyuncs.com')
        self.assertEqual(options['region_name'], 'oss-cn-hangzhou')
        self.assertEqual(options['access_key'], 'key-id')
        self.assertEqual(options['secret_key'], 'key-secret')
        self.assertEqual(options['location'], 'media')
        self.assertEqual(options['custom_domain'], 'cdn.example.com')
        self.assertEqual(options['default_acl'], 'private')
        self.assertEqual(options['querystring_expire'], 600)
        self.assertFalse(options['file_overwrite'])

    def test_build_options_filters_empty_values(self):
        """未配置的可选项不应出现在选项中。"""
        options = build_s3_options({'STORAGE_S3_BUCKET_NAME': 'campus-media'})

        self.assertEqual(options['bucket_name'], 'campus-media')
        self.assertNotIn('access_key', options)
        self.assertNotIn('endpoint_url', options)
        self.assertNotIn('custom_domain', options)
        self.assertEqual(options['addressing_style'], 'virtual')
        self.assertEqual(options['default_acl'], 'public-read')
        self.assertEqual(options['querystring_expire'], 3600)
