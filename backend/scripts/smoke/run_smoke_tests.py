#!/usr/bin/env python3
"""
冒烟测试运行器

自动完成以下步骤：
1. 以守护进程模式启动后端开发服务器
2. 等待健康检查接口就绪
3. 初始化测试数据
4. 运行全链路接口冒烟测试 (test_full_api.py)
5. 停止服务器并返回测试结果

用法：
    cd backend
    python scripts/smoke/run_smoke_tests.py

环境要求：
    - 已配置 .env 文件或对应环境变量
    - 端口 8000 未被占用（可通过 --port 指定）
"""

import argparse
import io
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# Windows 控制台默认 GBK 编码无法输出部分 Unicode 字符，强制使用 utf-8
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
START_SERVER = BASE_DIR / 'start_server.py'
TEST_SCRIPT = BASE_DIR / 'tests' / 'integration' / 'test_full_api.py'
CREATE_DATA_SCRIPT = BASE_DIR / 'scripts' / 'seed' / 'create_data.py'


def wait_for_health(host: str, port: int, timeout: int = 60) -> bool:
    """等待健康检查接口可用"""
    url = f'http://{host}:{port}/health/'
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get('status') == 'ok':
                    return True
        except Exception:
            pass
        time.sleep(1)
    return False


def is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((host, port)) == 0


def run_command(cmd: list, description: str, cwd: Path = BASE_DIR, env: dict | None = None) -> bool:
    print(f'\n>>> {description}')
    print(f"执行命令: {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        env=env
    )
    if result.returncode != 0:
        print(f'[FAIL] {description} 失败')
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return False
    if result.stdout:
        print(result.stdout)
    print(f'[OK] {description}')
    return True


def find_server_pid(host: str, port: int) -> int | None:
    """查找监听指定端口的 Python 进程 PID（用于守护进程模式关闭）"""
    try:
        import psutil
    except ImportError:
        return None

    for conn in psutil.net_connections(kind='inet'):
        if conn.status == psutil.CONN_LISTEN and conn.laddr.port == port:
            return conn.pid
    return None


def stop_server(host: str, port: int) -> None:
    print('\n>>> 停止后端服务器')
    try:
        import psutil
        pid = find_server_pid(host, port)
        if pid:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=10)
            print(f'[OK] 已停止服务器进程 (PID: {pid})')
        else:
            print('[WARN] 未找到监听端口的服务器进程')
    except ImportError:
        print('[WARN] 未安装 psutil，请手动关闭端口进程')
    except Exception as e:
        print(f'[WARN] 停止服务器时出错: {e}')


def main():
    parser = argparse.ArgumentParser(description='校园实时互动社区后端冒烟测试运行器')
    parser.add_argument('--host', default='127.0.0.1', help='服务器监听地址')
    parser.add_argument('--port', type=int, default=8000, help='服务器监听端口')
    parser.add_argument('--no-sync', action='store_true', help='跳过 uv 依赖同步')
    parser.add_argument('--keep-server', action='store_true', help='测试结束后保留服务器运行')
    args = parser.parse_args()

    print('=== 校园实时互动社区后端冒烟测试 ===')
    print(f'目标地址: http://{args.host}:{args.port}')

    if is_port_open(args.host, args.port):
        print(f'[FAIL] 端口 {args.port} 已被占用，请关闭占用进程后再试', file=sys.stderr)
        sys.exit(1)

    # 启动服务器（守护进程模式）
    server_cmd = [
        sys.executable, str(START_SERVER),
        '--bind', args.host,
        '--port', str(args.port),
        '--daemon',
        '--no-tests',
    ]
    if args.no_sync:
        server_cmd.append('--no-sync')

    if not run_command(server_cmd, '启动后端服务器'):
        sys.exit(1)

    try:
        if not wait_for_health(args.host, args.port, timeout=60):
            print('[FAIL] 健康检查接口未在 60 秒内就绪', file=sys.stderr)
            sys.exit(1)
        print('[OK] 健康检查接口已就绪')

        # 初始化测试数据
        if not run_command([sys.executable, str(CREATE_DATA_SCRIPT)], '初始化测试数据'):
            sys.exit(1)

        # 运行全链路接口测试
        test_env = os.environ.copy()
        test_env['SMOKE_TEST_BASE_URL'] = f'http://{args.host}:{args.port}/api'
        if not run_command([sys.executable, str(TEST_SCRIPT)], '运行全链路接口冒烟测试', env=test_env):
            sys.exit(1)

        print('\n=== 所有冒烟测试通过 ===')
    finally:
        if not args.keep_server:
            stop_server(args.host, args.port)


if __name__ == '__main__':
    main()
