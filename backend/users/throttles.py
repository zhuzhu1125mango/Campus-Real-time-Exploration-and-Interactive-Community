from rest_framework.throttling import SimpleRateThrottle


class LoginThrottle(SimpleRateThrottle):
    """登录相关接口限流（账号密码登录、邮箱验证码登录、手机验证码登录）。"""
    scope = 'login'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class CodeSendThrottle(SimpleRateThrottle):
    """验证码发送接口限流（邮箱验证码、手机验证码）。"""
    scope = 'code'

    def get_cache_key(self, request, view):
        # 未登录按 IP，已登录按用户 ID，防止同一用户刷不同目标
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class SearchThrottle(SimpleRateThrottle):
    """搜索接口限流。"""
    scope = 'search'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class WriteThrottle(SimpleRateThrottle):
    """写操作接口限流（创建、收藏、点赞、评分、报名等）。"""
    scope = 'write'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}
