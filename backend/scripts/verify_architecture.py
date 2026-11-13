"""架构改造验证脚本。

验证项：
1. HTTP ASGI 入口不加载 Channels WebSocket 路由
2. WS ASGI 入口仅加载 WebSocket 路由
3. Database Router 将读请求路由到 replica（或回退到 default）
4. Channel Layer 与 Cache 使用不同的 Redis 地址
5. Celery 应用可正常加载
6. Elasticsearch 配置与 Document 可加载
7. 缓存配置与统一缓存工具层可加载

运行方式：
    cd backend
    uv run python scripts/verify_architecture.py
"""

import os
import sys

# 将 backend 目录加入 Python 路径，确保可以从 scripts 目录直接运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


def check_asgi_http():
    """验证 HTTP ASGI 入口为原生 Django ASGIHandler，不加载 Channels 路由。"""
    print("[ASGI HTTP] 检查 config.asgi_http ...")
    from django.core.handlers.asgi import ASGIHandler
    from config.asgi_http import application

    assert isinstance(application, ASGIHandler), \
        "HTTP ASGI 入口应为 Django ASGIHandler，不应是 Channels ProtocolTypeRouter"
    print("  OK: HTTP 入口为原生 Django ASGIHandler，未加载 Channels 路由")


def check_asgi_ws():
    """验证 WS ASGI 入口只包含 websocket 协议。"""
    print("[ASGI WS] 检查 config.asgi_ws ...")
    from config.asgi_ws import application

    app_types = list(application.application_mapping.keys())
    assert app_types == ['websocket'], f"WS ASGI 应只包含 'websocket' 协议，当前为 {app_types}"
    print(f"  OK: WS 入口仅包含协议 {app_types}")


def check_database_router():
    """验证读写分离路由。"""
    print("[Database Router] 检查 config.db_router.PrimaryReplicaRouter ...")
    from django.conf import settings
    from config.db_router import PrimaryReplicaRouter

    router = PrimaryReplicaRouter()

    write_db = router.db_for_write(None)
    assert write_db == 'default', f"写请求应路由到 default，当前为 {write_db}"
    print(f"  OK: 写请求路由到 {write_db}")

    read_db = router.db_for_read(None)
    expected = 'replica' if 'replica' in settings.DATABASES else 'default'
    assert read_db == expected, f"读请求应路由到 {expected}，当前为 {read_db}"
    print(f"  OK: 读请求路由到 {read_db}")

    assert router.allow_relation(None, None) is True
    print("  OK: 允许跨库关系")

    assert router.allow_migrate('default', 'users') is True
    assert router.allow_migrate('replica', 'users') is False
    print("  OK: 仅允许在主库执行迁移")


def check_redis_split():
    """验证 Redis 拆分配置。"""
    print("[Redis] 检查 CHANNEL_LAYERS 与 CACHES 是否使用不同 Redis ...")
    from django.conf import settings

    channel_backend = settings.CHANNEL_LAYERS['default']['BACKEND']
    cache_backend = settings.CACHES['default']['BACKEND']
    cache_location = settings.CACHES['default'].get('LOCATION', 'memory')

    print(f"  Channel Layer backend: {channel_backend}")
    print(f"  Cache backend: {cache_backend}")
    print(f"  Cache location: {cache_location}")

    # 开发环境 DEBUG=True 时使用内存 Channel Layer 与内存缓存，跳过 Redis 地址校验
    if settings.DEBUG:
        print("  INFO: DEBUG=True，开发环境使用内存 Channel Layer / 缓存，跳过严格校验")
        return

    channel_hosts = settings.CHANNEL_LAYERS['default']['CONFIG']['hosts']
    print(f"  Channel Layer Redis: {channel_hosts}")
    assert channel_hosts != [cache_location], \
        "生产环境下 Channel Layer 与 Cache 应使用不同的 Redis 地址"
    print("  OK: Channel Layer 与 Cache 已拆分")


def check_celery(celery_app):
    """验证 Celery 应用可加载。"""
    print("[Celery] 检查 Celery 应用与任务发现 ...")
    registered_tasks = list(celery_app.tasks.keys())
    print(f"  已注册任务数: {len(registered_tasks)}")
    expected_tasks = [
        'users.tasks.send_notification_async',
        'send_notification_async',
        'users.tasks.update_user_points_async',
        'update_user_points_async',
        'search.tasks.index_object',
        'index_object',
    ]
    assert any(task in registered_tasks for task in expected_tasks), \
        f"未找到 expected task，已注册任务: {registered_tasks}"
    print("  OK: Celery 应用加载成功，示例任务已注册")


def check_notifications_points():
    """验证通知/积分异步任务与规则配置可加载。"""
    print("[Notifications/Points] 检查通知与积分异步化配置 ...")
    from users.points import POINTS_RULES, LEVEL_THRESHOLDS, calculate_level
    from users.tasks import update_user_points_async
    from notifications.notification_sender import create_notification

    # 检查核心积分规则
    required_actions = [
        'register', 'daily_checkin', 'complete_profile', 'verified',
        'post', 'reply', 'comment', 'like', 'liked',
    ]
    for action in required_actions:
        assert action in POINTS_RULES, f"缺少积分规则: {action}"
        assert POINTS_RULES[action] >= 0, f"积分规则不应为负: {action}"
    print(f"  积分规则: { {k: v for k, v in POINTS_RULES.items() if k in required_actions} }")

    # 检查等级规则
    assert len(LEVEL_THRESHOLDS) > 1
    assert calculate_level(0) == 1
    print(f"  等级阈值: {LEVEL_THRESHOLDS}")

    # 检查任务函数可调用
    assert callable(update_user_points_async)
    print("  OK: 通知/积分异步任务与规则配置正常")


def check_elasticsearch():
    """验证 Elasticsearch 配置与 Document 可加载。"""
    print("[Elasticsearch] 检查搜索配置 ...")
    from django.conf import settings
    from search.documents import DOCUMENT_REGISTRY

    hosts = settings.ELASTICSEARCH_HOSTS
    print(f"  ES hosts: {hosts}")
    assert hosts, "ELASTICSEARCH_HOSTS 不能为空"

    assert len(DOCUMENT_REGISTRY) >= 6, f"Document 注册数量异常: {len(DOCUMENT_REGISTRY)}"
    print(f"  已注册 Document: {list(DOCUMENT_REGISTRY.keys())}")

    from search.client import es_is_available
    if es_is_available():
        print("  OK: Elasticsearch 可连接")
    else:
        print("  INFO: Elasticsearch 当前不可用，但已配置降级策略")


def check_cache():
    """验证缓存配置与统一缓存工具层。"""
    print("[Cache] 检查缓存配置 ...")
    from django.conf import settings
    from django.core.cache import cache
    from core.cache_utils import (
        build_cache_key,
        cache_get,
        cache_set,
        invalidate_namespace,
        get_default_timeout,
    )

    cache_backend = settings.CACHES['default']['BACKEND']
    print(f"  Cache backend: {cache_backend}")

    if not settings.DEBUG:
        assert 'django_redis' in cache_backend, "生产环境应使用 django-redis 作为缓存后端"
        print("  OK: 生产环境使用 django-redis")

    # 验证 CACHE_UTILS 配置存在
    cache_utils = getattr(settings, 'CACHE_UTILS', {})
    assert 'CACHE_TIMEOUTS' in cache_utils, "CACHE_UTILS 中缺少 CACHE_TIMEOUTS 配置"
    assert 'CACHE_KEY_PREFIX' in cache_utils, "CACHE_UTILS 中缺少 CACHE_KEY_PREFIX 配置"
    print(f"  Cache timeouts: {cache_utils['CACHE_TIMEOUTS']}")
    print(f"  Cache key prefix: {cache_utils['CACHE_KEY_PREFIX']}")

    # 验证缓存读写与命名空间失效
    test_namespace = 'verify'
    test_key = build_cache_key(test_namespace, 'test')
    test_value = {'ok': True, 'timestamp': __import__('time').time()}

    invalidate_namespace(test_namespace)
    assert cache_set(test_key, test_value, timeout=60, namespace=test_namespace), "缓存写入失败"
    cached = cache_get(test_key, namespace=test_namespace)
    assert cached == test_value, f"缓存读取失败，期望值 {test_value}，实际值 {cached}"

    invalidate_namespace(test_namespace)
    after_invalidate = cache_get(test_key, default='miss', namespace=test_namespace)
    assert after_invalidate == 'miss', "命名空间失效后缓存应失效"

    print("  OK: 缓存读写与命名空间失效正常")
    print(f"  默认分层 TTL: hot={get_default_timeout('hot')}s, medium={get_default_timeout('medium')}s, cold={get_default_timeout('cold')}s")


def main():
    import django
    django.setup()

    # 必须在 Django setup 之后导入 Celery，否则 autodiscover_tasks 无法发现 tasks.py
    global app
    from config.celery import app as celery_app

    checks = [
        check_asgi_http,
        check_asgi_ws,
        check_database_router,
        check_redis_split,
        lambda: check_celery(celery_app),
        check_elasticsearch,
        check_cache,
        check_notifications_points,
    ]

    failed = False
    for check in checks:
        try:
            check()
        except Exception as exc:
            print(f"  FAILED: {exc}")
            failed = True
        print()

    if failed:
        print("验证未通过，请检查配置。")
        sys.exit(1)
    else:
        print("所有验证项通过。")
        sys.exit(0)


if __name__ == '__main__':
    main()
