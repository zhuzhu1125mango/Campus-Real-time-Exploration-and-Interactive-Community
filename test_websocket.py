#!/usr/bin/env python3
"""
测试WebSocket连接
"""
import websocket
import json
import time

# WebSocket服务器地址
ws_url = "ws://localhost:8000/ws/chat/"

# 连接回调
class WebSocketTest:
    def __init__(self):
        self.ws = None
    
    def on_open(self, ws):
        print("WebSocket连接已打开")
        # 发送测试消息
        test_message = {
            "type": "chat_message",
            "message": "测试消息"
        }
        ws.send(json.dumps(test_message))
        print("已发送测试消息")
    
    def on_message(self, ws, message):
        print(f"收到消息: {message}")
    
    def on_error(self, ws, error):
        print(f"WebSocket错误: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        print(f"WebSocket连接已关闭，状态码: {close_status_code}, 消息: {close_msg}")
    
    def run(self):
        # 创建WebSocket连接
        websocket.enableTrace(True)  # 启用跟踪，获取更详细的信息
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        # 运行WebSocket客户端
        try:
            print(f"尝试连接到: {ws_url}")
            self.ws.run_forever()
        except Exception as e:
            print(f"连接异常: {e}")

if __name__ == "__main__":
    test = WebSocketTest()
    test.run()
