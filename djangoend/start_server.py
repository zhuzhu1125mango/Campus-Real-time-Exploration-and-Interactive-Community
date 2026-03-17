#!/usr/bin/env python
"""
启动服务器脚本
在Windows环境中使用Django开发服务器
"""
import os
import sys

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')

try:
    import django
    django.setup()
    
    from django.core.management import execute_from_command_line
    
    # 使用Django开发服务器启动
    execute_from_command_line([sys.argv[0], 'runserver', '0.0.0.0:8000'])
    
except Exception as e:
    print(f"启动服务器时出错: {e}")
    sys.exit(1)
