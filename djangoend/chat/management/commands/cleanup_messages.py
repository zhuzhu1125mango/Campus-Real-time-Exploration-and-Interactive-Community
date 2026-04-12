from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from chat.models import ChatMessage
from users.models import Message as PrivateMessage


class Command(BaseCommand):
    """
    清理过期的聊天消息
    只保留最近7天的消息
    """
    help = '清理过期的聊天消息，只保留最近7天的消息'

    def handle(self, *args, **options):
        # 计算7天前的时间
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        # 清理实时聊天室消息
        chat_messages_deleted = ChatMessage.objects.filter(created_at__lt=seven_days_ago).delete()[0]
        
        # 清理私信消息
        private_messages_deleted = PrivateMessage.objects.filter(created_at__lt=seven_days_ago).delete()[0]
        
        self.stdout.write(self.style.SUCCESS(f'清理完成！删除了 {chat_messages_deleted} 条聊天室消息和 {private_messages_deleted} 条私信消息'))
