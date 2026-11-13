from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView


# 简单的健康检查
def health_check(request):
    return JsonResponse({"status": "ok"})

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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 