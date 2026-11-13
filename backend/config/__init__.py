import pymysql
pymysql.install_as_MySQLdb()

# 启动 Django 时自动加载 Celery 应用
from .celery import app as celery_app

__all__ = ('celery_app',)
