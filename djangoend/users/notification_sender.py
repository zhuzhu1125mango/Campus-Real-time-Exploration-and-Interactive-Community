from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from .notifications import Notification


def send_notification(notification):
    """
    发送实时通知
    当创建新通知时，通过WebSocket发送给用户
    """
    try:
        # 获取通道层
        channel_layer = get_channel_layer()
        
        # 构建通知数据
        notification_data = {
            'id': notification.id,
            'title': notification.title,
            'content': notification.content,
            'notification_type': notification.notification_type,
            'created_at': notification.created_at.isoformat(),
            'is_read': notification.is_read,
            'url': notification.url
        }
        
        # 如果有发送者，添加发送者信息
        if notification.sender:
            notification_data['sender'] = {
                'id': notification.sender.id,
                'username': notification.sender.username
            }
        
        # 发送通知到用户特定的频道
        user_group_name = f"user_{notification.recipient.id}"
        async_to_sync(channel_layer.group_send)(
            user_group_name,
            {
                'type': 'notification',
                'notification': notification_data
            }
        )
        
        # 发送未读通知数量更新
        unread_count = Notification.get_unread_count(notification.recipient)
        async_to_sync(channel_layer.group_send)(
            user_group_name,
            {
                'type': 'unread_notifications_update',
                'count': unread_count
            }
        )
        
    except Exception as e:
        # 记录错误但不影响主流程
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"发送通知时出错: {str(e)}")


def send_notification_to_user(user, title, content, notification_type='system', url=''):
    """
    创建并发送通知给用户
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if not isinstance(user, User):
        return
    
    # 创建通知
    notification = Notification.objects.create(
        recipient=user,
        title=title,
        content=content,
        notification_type=notification_type,
        url=url
    )
    
    # 发送实时通知
    send_notification(notification)
    
    return notification