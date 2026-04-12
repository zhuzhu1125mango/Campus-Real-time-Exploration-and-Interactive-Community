#!/usr/bin/env python3
"""
设置定时清理过期消息的任务
"""
import os
import platform
import subprocess


def setup_cron_job():
    """
    设置定时清理过期消息的任务
    """
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 构建管理命令路径
    manage_py_path = os.path.join(project_root, 'manage.py')
    
    # 构建命令
    command = f'python "{manage_py_path}" cleanup_expired_messages'
    
    if platform.system() == 'Windows':
        # Windows系统使用任务计划程序
        setup_windows_task(command, project_root)
    else:
        # Linux/Mac系统使用cron
        setup_cron_job_unix(command, project_root)


def setup_windows_task(command, project_root):
    """
    在Windows系统上设置任务计划程序
    """
    print("在Windows系统上设置任务计划程序...")
    
    # 使用schtasks命令创建任务
    task_name = "CleanupExpiredMessages"
    
    # 创建任务：每天凌晨1点执行
    schtasks_command = (
        f'schtasks /create /tn "{task_name}" /tr "{command}" /sc daily /st 01:00:00 '
        f'/ru SYSTEM /rl HIGHEST /f'
    )
    
    try:
        subprocess.run(schtasks_command, shell=True, check=True)
        print(f"任务计划已创建：{task_name}")
        print(f"任务将在每天凌晨1点执行")
    except subprocess.CalledProcessError as e:
        print(f"创建任务计划失败：{e}")


def setup_cron_job_unix(command, project_root):
    """
    在Linux/Mac系统上设置cron任务
    """
    print("在Linux/Mac系统上设置cron任务...")
    
    # 构建cron表达式：每天凌晨1点执行
    cron_expression = "0 1 * * *"
    
    # 构建完整的cron任务行
    cron_job = f"{cron_expression} cd {project_root} && {command} >> {project_root}/cleanup.log 2>&1"
    
    # 读取当前的crontab
    try:
        current_crontab = subprocess.run(
            ['crontab', '-l'],
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError:
        current_crontab = None
    
    # 检查任务是否已存在
    existing_jobs = current_crontab.stdout if current_crontab and current_crontab.returncode == 0 else ''
    
    if 'cleanup_expired_messages' in existing_jobs:
        print("任务已存在，跳过创建")
        return
    
    # 添加新任务
    new_crontab = existing_jobs + cron_job + '\n'
    
    # 写入crontab
    try:
        process = subprocess.Popen(
            ['crontab', '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=new_crontab)
        
        if process.returncode == 0:
            print("cron任务已创建")
            print(f"任务将在每天凌晨1点执行")
        else:
            print(f"创建cron任务失败：{stderr}")
    except Exception as e:
        print(f"创建cron任务失败：{e}")


if __name__ == "__main__":
    setup_cron_job()
