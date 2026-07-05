import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class WebSocketMessageService:
    def send_private_message(self, sender, receiver, message):
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("Channel layer 不可用，无法发送 WebSocket 消息")
            return False

        try:
            message_data = self._build_message_data(sender, receiver, message)
            room_group_name = self._get_room_group_name(sender, receiver)

            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'private_message',
                    **message_data
                }
            )

            logger.info(f"WebSocket 消息发送成功: {sender.username} -> {receiver.username}")
            return True

        except Exception as e:
            logger.error(f"WebSocket 消息发送失败: {str(e)}")
            return False

    def _build_message_data(self, sender, receiver, message):
        sender_avatar = self._get_avatar_url(sender)

        return {
            'id': message.id,
            'content': message.content,
            'sender_id': sender.id,
            'sender_username': sender.username,
            'sender_avatar': sender_avatar,
            'receiver_id': receiver.id,
            'receiver_username': receiver.username,
            'is_read': message.is_read,
            'created_at': message.created_at.isoformat()
        }

    def _get_room_group_name(self, sender, receiver):
        user_ids = sorted([str(sender.id), str(receiver.id)])
        return f"private_chat_{user_ids[0]}_{user_ids[1]}"

    def _get_avatar_url(self, user):
        if hasattr(user, 'avatar') and user.avatar:
            try:
                return user.avatar.url
            except Exception:
                pass
        return None


websocket_service = WebSocketMessageService()