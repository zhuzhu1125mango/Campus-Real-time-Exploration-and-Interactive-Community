from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import AnonymousUser
from urllib.parse import parse_qs
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class TokenAuthMiddleware:
    """
    用于 WebSocket 连接的 JWT Token 认证中间件。

    优先从 Sec-WebSocket-Protocol 子协议头读取 token，避免 token 出现在 URL 中
    被浏览器历史或服务器日志记录；同时保留对旧版 URL query string 的兼容。
    子协议格式: ['jwt', '<access_token>']
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        token = self._extract_token(scope)

        if token:
            logger.info("WebSocket认证中间件: 获取到token")
            try:
                access_token = AccessToken(token)
                user_id = access_token['user_id']
                user = await TokenAuthMiddleware.get_user(user_id)

                if user and user.is_active:
                    logger.info(f"WebSocket认证中间件: 认证成功，用户: {user.username} (ID: {user.id})")
                    scope['user'] = user
                else:
                    logger.warning("WebSocket认证中间件: 认证失败，用户不存在或已被禁用")
                    scope['user'] = AnonymousUser()
            except Exception as e:
                # token 过期或无效属于常见客户端状态，降级为警告避免污染日志
                logger.warning(f"WebSocket认证中间件: token无效或已过期 ({type(e).__name__}: {str(e)})")
                scope['user'] = AnonymousUser()
        else:
            logger.info("WebSocket认证中间件: 未提供token，使用匿名用户")
            scope['user'] = AnonymousUser()

        return await self.inner(scope, receive, send)

    def _extract_token(self, scope):
        """优先从子协议读取 token，其次从 query string 读取。"""
        subprotocols = scope.get('subprotocols', [])
        if len(subprotocols) >= 2 and subprotocols[0].lower() == 'jwt':
            return subprotocols[1]

        query_string = scope.get('query_string', b'').decode('utf-8')
        if query_string:
            query_params = parse_qs(query_string)
            if 'token' in query_params:
                return query_params['token'][0]
        return None

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