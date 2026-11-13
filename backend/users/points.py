"""积分规则统一配置。

集中管理各业务行为的积分值、等级阈值与描述文案，
供同步/异步积分更新逻辑统一使用。
"""

from django.utils.translation import gettext_lazy as _


# 行为 -> 积分值（正数表示奖励，负数表示扣除）
POINTS_RULES = {
    'register': 10,
    'login': 2,
    'complete_profile': 20,
    'verified': 50,
    'daily_checkin': 5,
    'consecutive_checkin_3': 5,
    'consecutive_checkin_7': 10,
    'post': 10,
    'reply': 5,
    'comment': 5,
    'like': 2,
    'liked': 3,
    'favorite': 2,
    'share': 5,
    'create_course': 15,
    'complete_course': 20,
    'system': 0,
    'admin': 0,
}


# 行为描述文案（用于 PointsRecord.description）
ACTION_DESCRIPTIONS = {
    'register': _('注册奖励'),
    'login': _('每日登录'),
    'complete_profile': _('完善个人资料'),
    'verified': _('完成身份认证'),
    'daily_checkin': _('每日签到'),
    'consecutive_checkin_3': _('连续签到3天额外奖励'),
    'consecutive_checkin_7': _('连续签到7天额外奖励'),
    'post': _('发布帖子'),
    'reply': _('发表回复'),
    'comment': _('发表评论'),
    'like': _('点赞'),
    'liked': _('内容被点赞'),
    'favorite': _('收藏'),
    'share': _('分享'),
    'create_course': _('创建课程'),
    'complete_course': _('完成课程学习'),
    'system': _('系统奖励'),
    'admin': _('管理员操作'),
}


# 等级阈值：累计积分达到对应值时升级到该等级
LEVEL_THRESHOLDS = [0, 50, 200, 500, 1000, 2000, 5000, 10000]


# 等级名称
LEVEL_NAMES = {
    1: _('新手'),
    2: _('初级学员'),
    3: _('中级学员'),
    4: _('高级学员'),
    5: _('学霸'),
    6: _('学神'),
    7: _('导师'),
    8: _('大师'),
}


def get_points_for_action(action: str) -> int:
    """获取指定行为的积分值。"""
    return POINTS_RULES.get(action, 0)


def get_action_description(action: str) -> str:
    """获取指定行为的默认描述。"""
    return ACTION_DESCRIPTIONS.get(action, action)


def calculate_level(points: int) -> int:
    """根据累计积分计算等级。"""
    level = 1
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if points >= threshold:
            level = i + 1
        else:
            break
    return level


def get_level_name(level: int) -> str:
    """根据等级获取名称。"""
    return LEVEL_NAMES.get(level, LEVEL_NAMES.get(1))
