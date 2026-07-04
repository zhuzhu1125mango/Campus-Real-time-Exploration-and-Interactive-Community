#!/usr/bin/env python
"""
清除聊天历史记录并禁用聊天记录保存功能
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from chat.models import ChatMessage
from users.messages import Message


def clear_chat_history():
    """清除实时聊天室的历史记录"""
    print("开始清除实时聊天室历史记录...")
    chat_message_count = ChatMessage.objects.count()
    ChatMessage.objects.all().delete()
    print(f"已删除 {chat_message_count} 条实时聊天记录")


def clear_friend_chat_history():
    """清除好友聊天的历史记录"""
    print("开始清除好友聊天历史记录...")
    try:
        friend_message_count = Message.objects.count()
        Message.objects.all().delete()
        print(f"已删除 {friend_message_count} 条好友聊天记录")
    except Exception as e:
        print(f"清除好友聊天记录时出错: {str(e)}")


def main():
    """主函数"""
    print("开始执行聊天记录清理操作...")
    clear_chat_history()
    clear_friend_chat_history()
    print("聊天记录清理操作完成！")


if __name__ == "__main__":
    main()
