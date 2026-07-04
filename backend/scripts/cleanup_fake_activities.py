#!/usr/bin/env python
"""
清理虚假动态数据的脚本
确保动态列表仅显示用户真实发布的内容
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.activities import Activity
from django.contrib.auth import get_user_model

User = get_user_model()

def cleanup_fake_activities():
    """
    清理虚假动态数据
    """
    print("开始清理虚假动态数据...")
    
    # 统计清理前的动态数量
    total_activities = Activity.objects.count()
    print(f"清理前共有 {total_activities} 条动态")
    
    # 识别并删除虚假动态
    # 这里假设虚假动态是没有用户关联的动态，或者内容为空的动态
    fake_activities = Activity.objects.filter(
        user__isnull=True  # 没有用户关联的动态
    )
    
    # 也可以删除内容为空的动态
    empty_content_activities = Activity.objects.filter(
        content__isnull=True
    )
    
    # 合并需要删除的动态
    fake_activities = fake_activities | empty_content_activities
    
    # 去重
    fake_activities = fake_activities.distinct()
    
    # 统计需要删除的动态数量
    fake_count = fake_activities.count()
    print(f"识别出 {fake_count} 条虚假动态")
    
    # 删除虚假动态
    if fake_count > 0:
        fake_activities.delete()
        print(f"已删除 {fake_count} 条虚假动态")
    
    # 统计清理后的动态数量
    remaining_activities = Activity.objects.count()
    print(f"清理后剩余 {remaining_activities} 条动态")
    print("虚假动态数据清理完成！")

if __name__ == "__main__":
    cleanup_fake_activities()
