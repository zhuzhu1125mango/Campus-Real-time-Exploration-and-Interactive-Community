"""
Celery 配置。

用于异步执行耗时任务：通知推送、短信/邮件发送、积分计算、搜索索引更新等。
Broker 默认使用 RabbitMQ；开发环境可回退到 Redis 或直接内存模式。
"""

import os
import importlib
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('campus_community')

# 从 Django settings 中读取 CELERY_* 配置
app.config_from_object('django.conf:settings', namespace='CELERY')


def _autodiscover_tasks():
    """
    显式遍历 INSTALLED_APPS 并导入 tasks 模块。
    Celery 自带的 autodiscover_tasks 在部分环境下无法自动发现，
    因此这里手动兜底，确保各 app 的 shared_task 都被注册。
    """
    from django.conf import settings

    for app_name in settings.INSTALLED_APPS:
        # 跳过 Django 内置和第三方库
        if app_name.startswith('django.') or app_name.startswith('rest_framework'):
            continue
        try:
            importlib.import_module(f'{app_name}.tasks')
        except ModuleNotFoundError:
            # 该 app 没有 tasks.py，属于正常情况
            pass
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(f"导入 {app_name}.tasks 失败: {exc}")


_autodiscover_tasks()
