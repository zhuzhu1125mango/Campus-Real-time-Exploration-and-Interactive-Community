#!/usr/bin/env python3
"""
启动服务器脚本
使用daphne服务器启动Django应用，支持WebSocket功能
"""

import os
import sys
import subprocess
import time

# 确保在正确的目录中运行
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DJANGO_DIR = os.path.join(BASE_DIR, 'djangoend')

# 切换到Django目录
os.chdir(DJANGO_DIR)

def check_dependencies():
    """检查必要的依赖是否安装"""
    print("检查依赖...")
    try:
        # 检查daphne是否安装
        subprocess.run([sys.executable, '-m', 'pip', 'show', 'daphne'], 
                      check=True, capture_output=True)
        print("✓ daphne已安装")
    except subprocess.CalledProcessError:
        print("✗ daphne未安装，正在安装...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'daphne'], 
                          check=True, capture_output=True)
            print("✓ daphne安装成功")
        except subprocess.CalledProcessError as e:
            print(f"✗ 安装daphne失败: {e}")
            sys.exit(1)

def start_server():
    """启动daphne服务器"""
    print("启动daphne服务器...")
    
    # 设置环境变量
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
    
    # 构建daphne命令
    cmd = [
        sys.executable, '-m', 'daphne',
        '-b', '0.0.0.0',
        '-p', '8000',
        'djangoProject.asgi:application'
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    # 启动服务器
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # 等待服务器启动
        time.sleep(3)
        
        # 检查服务器状态
        if process.poll() is None:
            print("✓ daphne服务器已成功启动！")
            print("服务器运行在 http://localhost:8000")
            print("WebSocket服务可用在 ws://localhost:8000/ws/chat/")
            print("\n按 Ctrl+C 停止服务器")
            
            # 保持服务器运行
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n正在停止服务器...")
                process.terminate()
                process.wait(timeout=5)
                print("✓ 服务器已停止")
        else:
            # 服务器启动失败，显示错误信息
            stdout, stderr = process.communicate()
            print("✗ 服务器启动失败:")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            sys.exit(1)
            
    except Exception as e:
        print(f"✗ 启动服务器时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=== 启动校园实时互动社区服务器 ===")
    check_dependencies()
    start_server()
