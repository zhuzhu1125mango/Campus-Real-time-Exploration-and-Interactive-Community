#!/usr/bin/env python
"""
启动服务器脚本
使用Uvicorn部署Django应用
"""
import os
import sys

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')

def start_server():
    try:
        import django
        django.setup()
        
        import uvicorn
        
        # 使用Uvicorn启动
        print(f"Starting server on port 8000")
        uvicorn.run(
            "djangoProject.asgi:application",
            host="0.0.0.0",
            port=8000,
            workers=1,  # Windows上使用单进程
            log_level="info",
            reload=False  # 生产环境禁用自动重载
        )
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"启动服务器时出错: {e}")
        sys.exit(1)

if __name__ == '__main__':
    start_server()
