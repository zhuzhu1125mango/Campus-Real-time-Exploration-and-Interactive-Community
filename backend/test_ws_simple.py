import asyncio
import json
import sys
import urllib.error
import urllib.request

import websockets.exceptions
from websockets.asyncio.client import connect

BASE_HTTP = "http://localhost:8000"
BASE_WS = "ws://localhost:8000"


def http_request(method: str, path: str, data: dict | None = None, headers: dict | None = None) -> dict:
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


async def main():
    token_data = http_request("POST", "/api/token/", {"username": "admin", "password": "admin123"})
    token = token_data.get("access")
    print(f"token: {token[:20]}...")

    ws_url = f"{BASE_WS}/ws/chat/"
    print(f"connecting to {ws_url}")
    try:
        async with connect(ws_url, subprotocols=["jwt", token]) as ws:
            print("connected")
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            print("received:", msg)
    except websockets.exceptions.InvalidStatus as e:
        print("status code:", e.response.status_code)
        body = getattr(e.response, "body", b"")
        print("body:", body.decode("utf-8", errors="replace")[:1000])
    except Exception as e:
        print("error:", type(e).__name__, e)


if __name__ == "__main__":
    asyncio.run(main())
