from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from chat.models import ChatMessage
from users.messages import Message
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    清理过期的聊天消息，保留最近7天的消息
    """
    help = '清理过期的聊天消息，保留最近7天的消息'

    def handle(self, *args, **options):
        # 计算7天前的时间
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        # 清理ChatMessage（实时聊天室消息）
        chat_message_count, _ = ChatMessage.objects.filter(
            created_at__lt=seven_days_ago
        ).delete()
        
        # 清理Message（私信消息）
        private_message_count, _ = Message.objects.filter(
            created_at__lt=seven_days_ago
        ).delete()
        
        # 输出清理结果
        self.stdout.write(self.style.SUCCESS(f'已清理 {chat_message_count} 条实时聊天室消息'))
        self.stdout.write(self.style.SUCCESS(f'已清理 {private_message_count} 条私信消息'))
        
        # 记录日志
        logger.info(f'清理过期消息：{chat_message_count}条实时聊天室消息，{private_message_count}条私信消息')
