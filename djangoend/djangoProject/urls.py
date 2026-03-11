from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.shortcuts import render

# 简单的健康检查
def health_check(request):
    return JsonResponse({"status": "ok"})

# WebSocket测试页面
def websocket_test(request):
    return render(request, 'websocket_test.html')

# 根路径欢迎页面
def home(request):
    return JsonResponse({
        "message": "欢迎使用校园实时互动社区 API",
        "version": "1.0.0",
        "endpoints": {
            "api": "/api/",
            "admin": "/admin/",
            "health": "/health/",
            "websocket_test": "/websocket-test/"
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
    
    # 添加根健康检查
    path('health/', health_check, name='health_check'),
    
    # WebSocket测试页面
    path('websocket-test/', websocket_test, name='websocket_test'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 