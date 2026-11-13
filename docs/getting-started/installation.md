# 安装

本文只解决「把依赖装好、把基础设施启动起来」。装完后请继续阅读 [快速开始](quickstart.md)。

## 1. 环境要求

| 依赖 | 版本/说明 |
|---|---|
| Python | 3.12.*（`backend/pyproject.toml` 已锁定） |
| uv | Python 依赖与虚拟环境管理 |
| Node.js | 18+ |
| pnpm | H5 前端依赖管理（不要使用 npm/yarn） |
| Docker + Docker Compose | 推荐用于运行 MySQL、Redis、RabbitMQ、Elasticsearch |
| MySQL | 8.0+，字符集 `utf8mb4` |
| Redis | 7+，建议 WS 与业务缓存分成两个实例 |
| RabbitMQ | 3.x，Celery Broker |
| Elasticsearch | 8.x + analysis-ik（可选，未启动时搜索降级为 MySQL LIKE） |
| HBuilderX / 微信开发者工具 | 仅小程序端需要 |

## 2. 获取代码

```bash
git clone <repository-url>
cd Campus-Real-time-Exploration-and-Interactive-Community
```

## 3. 安装后端依赖

```bash
cd backend
uv sync --frozen
```

说明：

- `--frozen` 严格按 `uv.lock` 安装，保证团队成员依赖一致。
- 需要可选开发依赖（如 Faker）时使用 `uv sync --frozen --extra dev`。
- 生产镜像使用 `uv sync --frozen --no-dev --extra prod`。

## 4. 安装前端依赖

```bash
cd frontend
pnpm install
```

## 5. 启动基础设施

推荐只用 Docker 跑基础设施，前后端在宿主机运行：

```bash
# 在仓库根目录执行
docker compose up -d mysql redis-ws redis-cache rabbitmq elasticsearch
```

端口映射：

| 服务 | 宿主机地址 | 用途 |
|---|---|---|
| MySQL | `127.0.0.1:3306` | 业务数据库 |
| Redis WS | `redis://127.0.0.1:6379/0` | Channels Channel Layer |
| Redis Cache | `redis://127.0.0.1:6380/1` | 业务缓存、Celery 结果 |
| RabbitMQ | `amqp://127.0.0.1:5672`，管理台 `15672` | Celery Broker |
| Elasticsearch | `http://127.0.0.1:9200` | 全局搜索 |

如果本机 6379 已被占用，修改 `docker-compose.yml` 中 `redis-ws` 的端口映射，
并同步修改 `backend/.env` 的 `REDIS_WS_URL`。

## 6. 创建数据库

MySQL 容器会自动创建 `MYSQL_DATABASE` 指定的库（默认 `university_exchange`）。
如果使用已有的 MySQL 实例，请手动创建：

```sql
CREATE DATABASE university_exchange CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 7. 准备环境变量

至少需要准备三个位置的配置：

| 位置 | 用途 | 模板 |
|---|---|---|
| `backend/.env` | Django 本地开发 | `backend/.env.example` |
| 根目录 `.env` | Docker Compose / 生产变量 | 根目录 `.env.example` |
| `frontend/.env.development` | H5 开发环境 | 仓库已提供 |
| `mp-weixin/.env` | 小程序本地开发 | `mp-weixin/.env.example` |

```bash
# 后端本地开发
cp backend/.env.example backend/.env
# 按实际环境填写 DJANGO_SECRET_KEY、数据库、Redis、RabbitMQ、ES
```

生成强随机密钥：

```bash
openssl rand -base64 64
# 或
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

完整变量说明见 [配置说明](configuration.md)。

## 8. 验证安装

```bash
cd backend
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
```

预期：

- `System check identified no issues`
- `No changes detected`（当前仓库不存在迁移漂移）

> 不要使用 `python manage.py runserver` 验证 WebSocket，它不支持 WebSocket。
> 请使用 `python start_server.py`，见 [快速开始](quickstart.md)。

## 下一步

- [快速开始](quickstart.md)
- [配置说明](configuration.md)
- [故障排查](../guides/troubleshooting.md)
