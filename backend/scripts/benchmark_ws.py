"""
WebSocket 连接压测脚本。

用于验证 WebSocket 服务独立部署后的并发承载能力。
支持两种模式：
1. 匿名连接公共聊天室
2. 使用 JWT Token 连接（需传入 --token）

运行方式：
    uv run python scripts/benchmark_ws.py --url ws://localhost:8001/ws/chat/public/ \
        --connections 100 --duration 30
"""

import argparse
import asyncio
import json
import time
import statistics
import websockets


class WSBenchmark:
    def __init__(self, url, connections, duration, token=None):
        self.url = url
        self.connections = connections
        self.duration = duration
        self.token = token
        self.connected = 0
        self.failed = 0
        self.messages_received = 0
        self.latencies = []
        self._lock = asyncio.Lock()

    def _build_url(self):
        if self.token:
            # 优先通过 query string 传递 token；生产环境建议使用 Sec-WebSocket-Protocol
            sep = '&' if '?' in self.url else '?'
            return f"{self.url}{sep}token={self.token}"
        return self.url

    async def _worker(self, worker_id):
        url = self._build_url()
        try:
            async with websockets.connect(url, open_timeout=10) as ws:
                async with self._lock:
                    self.connected += 1

                start = time.time()
                while time.time() - start < self.duration:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=5)
                        self.messages_received += 1
                    except asyncio.TimeoutError:
                        continue

                    try:
                        data = json.loads(msg)
                        if data.get('type') == 'welcome':
                            self.latencies.append(time.time() - start)
                    except json.JSONDecodeError:
                        pass
        except Exception as exc:
            async with self._lock:
                self.failed += 1
            print(f"Worker {worker_id} failed: {exc}")

    async def run(self):
        print(f"开始压测: url={self.url}, connections={self.connections}, duration={self.duration}s")
        start = time.time()

        tasks = [self._worker(i) for i in range(self.connections)]
        await asyncio.gather(*tasks)

        elapsed = time.time() - start
        print(f"\n压测完成，总耗时: {elapsed:.2f}s")
        print(f"成功连接: {self.connected}")
        print(f"失败连接: {self.failed}")
        print(f"接收消息数: {self.messages_received}")
        if self.latencies:
            print(f"Welcome 消息延迟: avg={statistics.mean(self.latencies):.3f}s, "
                  f"max={max(self.latencies):.3f}s, min={min(self.latencies):.3f}s")


def main():
    parser = argparse.ArgumentParser(description="WebSocket 并发压测")
    parser.add_argument("--url", default="ws://localhost:8001/ws/chat/public/", help="WebSocket URL")
    parser.add_argument("--connections", type=int, default=100, help="并发连接数")
    parser.add_argument("--duration", type=int, default=30, help="单个连接保持时间（秒）")
    parser.add_argument("--token", default=None, help="JWT access token（可选）")

    args = parser.parse_args()

    benchmark = WSBenchmark(
        url=args.url,
        connections=args.connections,
        duration=args.duration,
        token=args.token,
    )
    asyncio.run(benchmark.run())


if __name__ == '__main__':
    main()
