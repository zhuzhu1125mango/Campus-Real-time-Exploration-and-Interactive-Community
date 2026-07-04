import asyncio
import json
import sys
import urllib.error
import urllib.request

from websockets.asyncio.client import connect

BASE_HTTP = "http://localhost:8000"
BASE_WS = "ws://localhost:8000"


def http_request(method: str, path: str, data: dict | None = None) -> dict:
    url = f"{BASE_HTTP}{path}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


async def main():
    print("Getting token...")
    try:
        token_data = http_request("POST", "/api/token/", {"username": "admin", "password": "admin123"})
    except Exception as e:
        print(f"Failed to get token: {e}")
        return 1
    token = token_data.get("access")
    print(f"Token: {token[:20]}...")

    ws_url = f"{BASE_WS}/ws/chat/"
    print(f"Connecting to {ws_url}")
    try:
        async with connect(ws_url, subprotocols=["jwt", token]) as ws:
            print("Connected")
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            print("Received:", msg)
    except Exception as e:
        print(f"WebSocket error: {type(e).__name__}: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
