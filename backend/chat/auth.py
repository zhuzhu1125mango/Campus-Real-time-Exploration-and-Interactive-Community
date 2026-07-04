from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    """
    自定义JWT认证中间件用于WebSocket连接
    """
    async def __call__(self, scope, receive, send):
        # 从查询字符串中提取token
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        
        token = query_params.get('token', [None])[0]
        scope['user'] = AnonymousUser()
        
        if token:
            try:
                # 解析JWT token
                access_token = AccessToken(token)
                user_id = access_token.payload.get('user_id')
                
                if user_id:
                    scope['user'] = await get_user(user_id)
                    logger.info(f"JWT认证成功，用户ID: {user_id}")
            except Exception as e:
                logger.error(f"JWT认证失败: {str(e)}")
        else:
            # 允许匿名连接（适用于开发测试）
            logger.warning("无token提供，允许匿名连接")
        
        return await super().__call__(scope, receive, send)

def JWTAuthMiddlewareStack(inner):
    """辅助函数用于构造中间件堆栈"""
    return JWTAuthMiddleware(inner) 