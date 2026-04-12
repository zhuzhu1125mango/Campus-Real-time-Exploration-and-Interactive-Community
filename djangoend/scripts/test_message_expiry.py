#!/usr/bin/env python3
"""
测试消息过期清理功能
"""
import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')

# 初始化Django
django.setup()

from chat.models import ChatMessage
from users.messages import Message
from users.models import User


def test_cleanup_logic():
    """
    直接测试清理逻辑，不依赖数据库操作
    """
    print("=== 测试清理逻辑 ===")
    
    # 计算7天前的时间
    now = timezone.now()
    seven_days_ago = now - timedelta(days=7)
    
    print(f"当前时间: {now}")
    print(f"7天前: {seven_days_ago}")
    
    # 测试时间比较逻辑
    test_times = [
        now - timedelta(days=8),  # 过期
        now - timedelta(days=7, hours=1),  # 过期
        now - timedelta(days=7),  # 刚好7天，不过期
        now - timedelta(days=6),  # 不过期
        now - timedelta(days=1),  # 不过期
    ]
    
    print("\n测试时间比较：")
    for test_time in test_times:
        is_expired = test_time < seven_days_ago
        print(f"时间: {test_time}, 是否过期: {is_expired}")
    
    print("\n清理逻辑测试完成")

def test_command_import():
    """
    测试清理命令是否能正确导入和执行
    """
    print("\n=== 测试清理命令导入 ===")
    
    try:
        from chat.management.commands.cleanup_expired_messages import Command
        print("成功导入清理命令")
        
        # 测试命令初始化
        command = Command()
        print("成功初始化清理命令")
        
        return True
    except Exception as e:
        print(f"导入清理命令失败: {e}")
        return False

def main():
    """
    主函数
    """
    print("=== 测试消息过期清理功能 ===")
    
    # 测试清理逻辑
    test_cleanup_logic()
    
    # 测试命令导入
    test_command_import()
    
    # 运行清理命令
    print("\n=== 运行清理命令 ===")
    from chat.management.commands.cleanup_expired_messages import Command
    command = Command()
    command.handle()
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    main()
