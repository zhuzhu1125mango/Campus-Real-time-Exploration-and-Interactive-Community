from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import AnonymousUser
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class TokenAuthMiddleware:
    """
    用于WebSocket连接的Token认证中间件
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # 从查询字符串中获取token
        query_string = scope.get('query_string', b'').decode('utf-8')
        token = None
        
        if query_string:
            from urllib.parse import parse_qs
            query_params = parse_qs(query_string)
            if 'token' in query_params:
                token = query_params['token'][0]
        
        logger.info(f"WebSocket认证中间件: 获取到token: {token}")
        
        # 验证token
        if token:
            try:
                access_token = AccessToken(token)
                user_id = access_token['user_id']
                user = await self.get_user(user_id)
                
                if user:
                    logger.info(f"WebSocket认证中间件: 认证成功，用户: {user.username} (ID: {user.id})")
                    scope['user'] = user
                else:
                    logger.warning("WebSocket认证中间件: 认证失败，用户不存在")
                    scope['user'] = AnonymousUser()
            except Exception as e:
                logger.error(f"WebSocket认证中间件: 认证失败: {str(e)}")
                scope['user'] = AnonymousUser()
        else:
            logger.info("WebSocket认证中间件: 未提供token，使用匿名用户")
            scope['user'] = AnonymousUser()
        
        return await self.inner(scope, receive, send)

    @staticmethod
    async def get_user(user_id):
        """
        异步获取用户
        """
        try:
            from asgiref.sync import sync_to_async
            get_user_sync = sync_to_async(User.objects.get)
            return await get_user_sync(id=user_id)
        except User.DoesNotExist:
            return None