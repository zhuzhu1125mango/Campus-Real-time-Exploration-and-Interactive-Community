"""微信小程序服务：code2session、access_token 与订阅消息发送。

未配置 ``WECHAT_APPID`` / ``WECHAT_SECRET`` 时所有方法安全降级，不抛异常。
"""

import json
import logging
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

CACHE_KEY = 'wechat:access_token'
# 通知类型 -> 订阅消息模板配置键
NOTIFICATION_TEMPLATE_MAP = {
    'content_comment': 'comment',
    'message': 'message',
    'interaction': 'interaction',
    'course_reminder': 'reminder',
}


def _config():
    return (
        getattr(settings, 'WECHAT_APPID', ''),
        getattr(settings, 'WECHAT_SECRET', ''),
    )


def is_configured():
    appid, secret = _config()
    return bool(appid and secret)


def template_key_for(notification_type):
    """返回通知类型对应的模板键，没有则返回 None。"""
    return NOTIFICATION_TEMPLATE_MAP.get(notification_type)


def get_template_id(key):
    templates = getattr(settings, 'WECHAT_SUBSCRIBE_TEMPLATES', {}) or {}
    return templates.get(key) or ''


def configured_template_keys():
    templates = getattr(settings, 'WECHAT_SUBSCRIBE_TEMPLATES', {}) or {}
    return [key for key, value in templates.items() if value]


def _http_json(url, payload=None):
    body = json.dumps(payload).encode('utf-8') if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        headers={'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode('utf-8'))


def code_to_openid(code):
    """用 wx.login 的 code 换取 openid。失败返回 None。"""
    appid, secret = _config()
    if not code or not appid or not secret:
        return None

    query = urllib.parse.urlencode({
        'appid': appid,
        'secret': secret,
        'js_code': code,
        'grant_type': 'authorization_code',
    })
    try:
        data = _http_json(f'https://api.weixin.qq.com/sns/jscode2session?{query}')
    except Exception:
        logger.exception('微信 code2session 请求失败')
        return None

    if data.get('errcode'):
        logger.warning('微信 code2session 返回错误: %s', data)
        return None
    return data.get('openid')


def get_access_token(force=False):
    """获取并缓存小程序 access_token。"""
    if not force:
        cached = cache.get(CACHE_KEY)
        if cached:
            return cached

    appid, secret = _config()
    if not appid or not secret:
        return None

    query = urllib.parse.urlencode({
        'grant_type': 'client_credential',
        'appid': appid,
        'secret': secret,
    })
    try:
        data = _http_json(f'https://api.weixin.qq.com/cgi-bin/token?{query}')
    except Exception:
        logger.exception('获取微信 access_token 失败')
        return None

    token = data.get('access_token')
    if not token:
        logger.warning('微信 access_token 响应异常: %s', data)
        return None

    expires_in = int(data.get('expires_in', 7200))
    cache.set(CACHE_KEY, token, max(expires_in - 300, 60))
    return token


def build_notification_data(notification):
    """构造订阅消息 data，约定模板字段为 thing1/thing2/time3。"""
    title = (notification.title or '')[:20]
    content = (notification.content or '')[:20]
    created = timezone.localtime(notification.created_at).strftime('%Y-%m-%d %H:%M')
    return {
        'thing1': title,
        'thing2': content,
        'time3': created,
    }


def send_subscribe_message(openid, template_id, data, page=None):
    """发送订阅消息，成功返回 True。"""
    if not openid or not template_id:
        return False

    payload = {
        'touser': openid,
        'template_id': template_id,
        'data': {key: {'value': value} for key, value in data.items()},
    }
    if page:
        payload['page'] = page

    for attempt in range(2):
        token = get_access_token(force=attempt > 0)
        if not token:
            return False
        url = f'https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={token}'
        try:
            result = _http_json(url, payload)
        except Exception:
            logger.exception('发送微信订阅消息失败')
            return False

        if result.get('errcode') == 0:
            return True

        # access_token 失效时刷新后重试一次
        if result.get('errcode') in (40001, 42001) and attempt == 0:
            continue
        logger.warning('微信订阅消息发送失败: %s', result)
        return False

    return False
