import asyncio
import json
import sys
import urllib.error
import urllib.request

import websockets.exceptions
from websockets.asyncio.client import connect

BASE_HTTP = "http://localhost:8080"
BASE_WS = "ws://localhost:8080"

# 默认测试账号，可通过命令行参数覆盖
TEST_USERNAME = sys.argv[1] if len(sys.argv) > 1 else "admin"
TEST_PASSWORD = sys.argv[2] if len(sys.argv) > 2 else "admin123"


def http_request(method: str, path: str, data: dict | None = None, headers: dict | None = None) -> dict:
    """发送 HTTP 请求并返回 JSON 响应。"""
    url = f"{BASE_HTTP}{path}"
    req_headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


def get_token(username: str, password: str) -> str:
    """通过 JWT token 接口获取 access token。"""
    data = http_request("POST", "/api/token/", {"username": username, "password": password})
    token = data.get("access") or data.get("token") or data.get("access_token")
    if not token:
        raise RuntimeError(f"登录响应中未找到 token: {data}")
    return token


async def test_public_chat(token: str):
    """测试公共聊天室 WebSocket。"""
    ws_url = f"{BASE_WS}/ws/chat/"
    print(f"[public] 连接 {ws_url}")
    try:
        async with connect(ws_url, subprotocols=["jwt", token]) as ws:
            print("[public] connected")
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            print("[public] received:", msg)
    except websockets.exceptions.InvalidStatus as e:
        print("[public] status code:", e.response.status_code)
        body = getattr(e.response, "body", b"")
        print("[public] body:", body.decode("utf-8", errors="replace")[:1000])
    except Exception as e:
        print("[public] error:", type(e).__name__, e)


async def test_private_chat(token: str, target_user_id: int):
    """测试私聊 WebSocket。"""
    ws_url = f"{BASE_WS}/ws/chat/private/{target_user_id}/"
    print(f"[private] 连接 {ws_url}")
    try:
        async with connect(ws_url, subprotocols=["jwt", token]) as ws:
            print("[private] connected")
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            print("[private] received:", msg)
    except websockets.exceptions.InvalidStatus as e:
        print("[private] status code:", e.response.status_code)
        body = getattr(e.response, "body", b"")
        print("[private] body:", body.decode("utf-8", errors="replace")[:1000])
    except Exception as e:
        print("[private] error:", type(e).__name__, e)


async def main():
    token = get_token(TEST_USERNAME, TEST_PASSWORD)
    print(f"获取 token 成功: {token[:20]}...")

    me = http_request("GET", "/api/users/users/me/", headers={"Authorization": f"Bearer {token}"})
    my_id = me.get("id")
    print(f"当前用户: {me.get('username')} (ID: {my_id})")

    # 找一个其他用户作为私聊目标（没有则跳过）
    target_id = None
    try:
        users_data = http_request("GET", "/api/users/users/", headers={"Authorization": f"Bearer {token}"})
        users = users_data if isinstance(users_data, list) else users_data.get("results", users_data.get("data", []))
        for u in users:
            if u.get("id") != my_id:
                target_id = u.get("id")
                break
    except Exception as e:
        print(f"获取用户列表失败: {e}")

    await test_public_chat(token)
    if target_id:
        await test_private_chat(token, target_id)
    else:
        print("未找到其他用户，跳过私聊测试")


if __name__ == "__main__":
    asyncio.run(main())
