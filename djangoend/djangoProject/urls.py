from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

# Swagger文档配置 (暂时注释，等待安装drf-yasg)
# from rest_framework import permissions
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi

# 创建Swagger schema视图
# schema_view = get_schema_view(
#    openapi.Info(
#       title="校园实时互动社区 API",
#       default_version='v1',
#       description="校园实时互动社区的RESTful API文档",
#       terms_of_service="https://www.example.com/terms/",
#       contact=openapi.Contact(email="contact@example.com"),
#       license=openapi.License(name="BSD License"),
#    ),
#    public=True,
#    permission_classes=(permissions.AllowAny,),
# )

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
    
    # Simple JWT 端点
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Swagger文档 (暂时注释，等待安装drf-yasg)
    # path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # 添加根健康检查
    path('health/', health_check, name='health_check'),
    
    # WebSocket测试页面
    path('websocket-test/', websocket_test, name='websocket_test'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 