# 快速开始

目标：在本地启动后端 HTTP/WebSocket、Celery、H5 前端，并完成一次健康检查。
前置条件见 [安装](installation.md)。

## 1. 启动顺序

```text
MySQL / Redis / RabbitMQ / Elasticsearch
        ↓
Django HTTP + WebSocket（start_server.py）
        ↓
Celery Worker
        ↓
H5 前端（pnpm dev） / 微信小程序
```

## 2. 启动后端

```bash
cd backend
python start_server.py
```

`start_server.py` 会执行依赖检查、数据库迁移、静态文件收集、端口检查等初始化，
最终使用 **uvicorn 启动 ASGI 应用**，同时提供 HTTP 与 WebSocket 能力。

常用参数：

| 参数 | 作用 |
|---|---|
| `--no-tests` | 跳过启动前自动测试，加快启动 |
| `--no-reload` | 关闭热加载，适合稳定调试 |
| `--create-admin` | 创建默认超级用户 `admin/admin123` |
| `--daphne` | 改用 Daphne 启动 |

启动成功：

| 能力 | 地址 |
|---|---|
| HTTP API | `http://localhost:8000` |
| 健康检查 | `http://localhost:8000/api/health/` |
| WebSocket | `ws://localhost:8000/ws/chat/public/` |
| 管理后台 | `http://localhost:8000/admin/` |

> 不要使用 `python manage.py runserver`，Django 原生开发服务器不支持 WebSocket。

## 3. 启动 Celery Worker

积分、通知推送、Elasticsearch 索引更新都是异步任务。另开一个终端：

```bash
cd backend
uv run celery -A config worker --loglevel info --concurrency 2
```

如需定时任务调度器（当前没有配置周期性任务，只有需要时再启动）：

```bash
cd backend
uv run celery -A config beat --loglevel info
```

## 4. 启动 H5 前端

```bash
cd frontend
pnpm dev
```

默认地址：`http://localhost:5173`。

Vite 已配置代理：

| 前缀 | 目标 |
|---|---|
| `/api` | `http://localhost:8000` |
| `/ws` | `ws://localhost:8000` |
| `/media` | `http://localhost:8000` |
| `/health` | `http://localhost:8000` |

因此本地开发时前端直接请求 `/api/...` 即可，无需修改 API 域名。

## 5. 启动微信小程序

1. 复制 `mp-weixin/.env.example` 为 `mp-weixin/.env`。
2. 修改 `VUE_APP_API_BASE_URL`（包含 `/api` 后缀）与 `VUE_APP_WS_BASE_URL`（以 `/ws/chat` 结尾）。
3. 使用 HBuilderX 打开 `mp-weixin/`，运行到微信开发者工具。
4. 在微信开发者工具中确认「不校验合法域名」仅在本地开发时开启。

示例：

```env
VUE_APP_API_BASE_URL=http://192.168.1.10:8000/api
VUE_APP_WS_BASE_URL=ws://192.168.1.10:8000/ws/chat
```

## 6. 验证

### 6.1 健康检查

```bash
curl http://localhost:8000/api/health/
```

预期：

```json
{"status": "ok"}
```

### 6.2 登录获取 Token

```bash
curl -X POST http://localhost:8000/api/users/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

预期返回 `access`、`refresh` 与 `user`。

### 6.3 验证 WebSocket

在浏览器控制台执行：

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat/public/', ['jwt', '<access-token>'])
ws.onmessage = e => console.log(JSON.parse(e.data))
```

预期先收到 `auth_success`、`unread_notifications`、`welcome` 等消息。

### 6.4 验证异步任务

登录后调用签到接口：

```bash
curl -X POST http://localhost:8000/api/users/users/daily_checkin/ \
  -H "Authorization: Bearer <access-token>"
```

在 Celery Worker 终端应看到积分任务日志；随后 `GET /api/users/users/me/`
中的 `points` 会更新（异步任务存在毫秒级延迟）。

## 7. 常见启动问题

| 现象 | 处理 |
|---|---|
| `DJANGO_SECRET_KEY 环境变量未设置` | 检查 `backend/.env` |
| 端口 8000 被占用 | 修改启动参数或释放端口 |
| WebSocket 连接 4001 | 未携带有效 JWT，检查 `jwt` 子协议或 `?token=` |
| WebSocket 连接 4003 | 私聊双方不是好友 |
| 前端 401 反复跳登录 | 检查 refresh token 与 `/api/token/refresh/` |
| 搜索报 ES 连接失败 | 属预期降级，见 [故障排查](../guides/troubleshooting.md) |

## 下一步

- [配置说明](configuration.md)
- [开发指南](../guides/development.md)
- [API 参考](../reference/api/README.md)
