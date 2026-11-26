from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView


# 健康检查：默认仅返回存活状态；?deep=1 时检查依赖组件
def health_check(request):
    if request.GET.get('deep') != '1':
        return JsonResponse({"status": "ok"})

    checks = {
        'database': _check_database,
        'cache': _check_cache,
        'elasticsearch': _check_elasticsearch,
    }
    components = {}
    for name, checker in checks.items():
        try:
            checker()
            components[name] = 'ok'
        except Exception:
            components[name] = 'error'

    healthy = all(value == 'ok' for value in components.values())
    return JsonResponse(
        {
            'status': 'ok' if healthy else 'degraded',
            'components': components,
        },
        status=200 if healthy else 503,
    )


def _check_database():
    from django.db import connection
    connection.ensure_connection()


def _check_cache():
    from django.core.cache import cache
    key = 'health:ping'
    cache.set(key, '1', 5)
    if cache.get(key) != '1':
        raise RuntimeError('cache read/write failed')


def _check_elasticsearch():
    from search.client import es_is_available
    if not es_is_available():
        raise RuntimeError('elasticsearch unavailable')

# 根路径欢迎页面
def home(request):
    return JsonResponse({
        "message": "欢迎使用校园实时互动社区 API",
        "version": "1.0.0",
        "endpoints": {
            "api": "/api/",
            "admin": "/admin/",
            "health": "/api/health/"
        },
        "documentation": {
            "swagger": "/api/swagger/",
            "redoc": "/api/redoc/"
        }
    })

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('forum.urls')),
    path('api/users/', include('users.urls')),
    path('api/schools/', include('schools.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/content/', include('content.urls')),
    path('api/learning/', include('learning.urls')),
    path('api/search/', include('search.urls')),
    path('api/feed/', include('feed.urls')),
    
    # Simple JWT 端点
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # 添加健康检查
    path('api/health/', health_check, name='api_health_check'),
    path('health/', health_check, name='health_check'),

    # OpenAPI / Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 