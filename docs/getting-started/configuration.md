# 配置说明

本文按「后端 → H5 → 小程序 → Docker Compose」列出当前代码实际读取的配置项。
默认值来自 `backend/config/settings.py`，示例值来自 `backend/.env.example`、根目录 `.env.example`。

## 1. 配置加载顺序

后端启动时由 `config/settings.py` 调用 `load_dotenv()` 读取 `backend/.env`。

- `load_dotenv()` 默认 **不覆盖** 已存在的系统环境变量，因此：真实环境变量 > `.env` 文件 > 代码默认值。
- Docker Compose 通过 `environment` 注入变量，优先级高于容器内 `.env`。
- 生产环境必须显式设置 `DJANGO_SECRET_KEY`，否则启动直接抛出 `ImproperlyConfigured`。

## 2. 后端环境变量

### 2.1 Django 基础

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | 是 | 无 | 生产环境使用 64 位以上强随机值 |
| `DJANGO_DEBUG` | 否 | `False` | 仅当值为字符串 `True` 时开启 |
| `ALLOWED_HOSTS` | 否 | `localhost,127.0.0.1` | 逗号分隔 |
| `CORS_ALLOWED_ORIGINS` | 否 | 本地 5173/5174/5175/3000/8080/8081 | 逗号分隔，生产必须显式配置 |

### 2.2 数据库

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DB_ENGINE` | `django.db.backends.mysql` | 仅支持 MySQL 时自动附加 utf8mb4 选项 |
| `DB_NAME` | `university_exchange` | 数据库名 |
| `DB_USER` / `DB_PASSWORD` | `root` / `123456` | 生产必须修改 |
| `DB_HOST` / `DB_PORT` | `localhost` / `3306` | |
| `DB_CONN_MAX_AGE` | `600` | 连接复用秒数 |
| `DB_REPLICA_HOST` | 空 | 为空时不启用读写分离 |
| `DB_REPLICA_NAME` / `DB_REPLICA_USER` / `DB_REPLICA_PASSWORD` | 回退主库配置 | 从库连接 |
| `DB_REPLICA_PORT` | 回退主库端口 | |
| `DB_REPLICA_CONN_MAX_AGE` | `600` | |

读写分离由 `config/db_router.py` 的 `PrimaryReplicaRouter` 实现：
读走 `replica`，写走 `default`；未配置从库时读请求回退主库。

### 2.3 Redis 与缓存

| 变量 | 默认值 | 说明 |
|---|---|---|
| `REDIS_URL` | `redis://localhost:6379/0` | 兼容旧配置 |
| `REDIS_WS_URL` | 回退 `REDIS_URL` | Channels Channel Layer 专用 |
| `REDIS_CACHE_URL` | 回退 `REDIS_URL`（默认 `redis://localhost:6379/1`） | 业务缓存、Celery 结果 |
| `CACHE_KEY_PREFIX` | `campus` | 缓存 key 前缀 |

> `DEBUG=True` 时缓存使用 LocMemCache、Channel Layer 使用 InMemoryChannelLayer，
> 只适合单进程开发；生产环境强制使用 Redis。

### 2.4 Celery

| 变量 | 默认值 | 说明 |
|---|---|---|
| `RABBITMQ_URL` | 空 | Celery Broker 的回退来源 |
| `CELERY_BROKER_URL` | 回退 `RABBITMQ_URL`，再回退 `REDIS_CACHE_URL` | Broker |
| `CELERY_RESULT_BACKEND` | `REDIS_CACHE_URL` | 任务结果后端 |
| `CELERY_TASK_ALWAYS_EAGER` | `False` | 设为 `True` 时任务同步执行，仅用于测试/旧 Redis |

### 2.5 Elasticsearch

| 变量 | 默认值 | 说明 |
|---|---|---|
| `ELASTICSEARCH_HOSTS` | `http://localhost:9200` | 逗号分隔多节点 |
| `ELASTICSEARCH_TIMEOUT` | `10` | 秒 |
| `ELASTICSEARCH_FALLBACK_TO_DB` | `True` | ES 不可用时降级 MySQL LIKE |
| `ELASTICSEARCH_INDEX_PREFIX` | `campus` | 索引名前缀，如 `campus_schools` |

### 2.6 短信与媒体

| 变量 | 默认值 | 说明 |
|---|---|---|
| `SMS_ENABLED` | `False` | 设为 `True` 后调用阿里云短信发送真实验证码 |
| `ALIYUN_ACCESS_KEY_ID` | 空 | 仅在启用短信时使用 |
| `ALIYUN_ACCESS_KEY_SECRET` | 空 | |
| `ALIYUN_SMS_SIGN_NAME` | 空 | |
| `ALIYUN_SMS_TEMPLATE_CODE` | 空 | |
| `MEDIA_URL` / `STATIC_URL` | `/media/` / `/static/` | Django 侧固定配置，环境变量未实际读取 |

> 未设置 `SMS_ENABLED=True` 时走开发模式验证码，不调用阿里云短信。

### 2.7 微信小程序

| 变量 | 默认值 | 说明 |
|---|---|---|
| `WECHAT_APPID` | 空 | 小程序 AppID，订阅消息与 code2session 使用 |
| `WECHAT_SECRET` | 空 | 小程序 AppSecret |
| `WECHAT_TEMPLATE_COMMENT` | 空 | “新评论”订阅消息模板 ID |
| `WECHAT_TEMPLATE_MESSAGE` | 空 | “新私信”模板 ID |
| `WECHAT_TEMPLATE_INTERACTION` | 空 | “点赞/好友请求”模板 ID |
| `WECHAT_TEMPLATE_REMINDER` | 空 | “学习提醒”模板 ID（可选） |

模板字段约定为 `thing1` / `thing2` / `time3`，详见
[小程序指南](../guides/mini-program.md#3-订阅消息)。

### 2.8 监控与上传安全（可选）

仅在启用 `--profile monitoring` 或 `--profile security` 时需要：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `GRAFANA_ADMIN_PASSWORD` | `admin` | Grafana 初始管理员密码 |
| `MYSQLD_EXPORTER_USER` | `exporter` | MySQL 监控账号 |
| `MYSQLD_EXPORTER_PASSWORD` | `exporter` | MySQL 监控账号密码 |
| `ANTIVIRUS_ENABLED` | `False` | 是否开启上传文件病毒扫描（fail-closed） |
| `CLAMAV_HOST` | `clamav` | ClamAV 服务地址 |
| `CLAMAV_PORT` | `3310` | clamd 端口 |
| `CLAMAV_TIMEOUT` | `10` | 扫描超时（秒） |

监控与日志聚合见 [运维手册](../guides/operations.md#10-监控-prometheus--grafana)，
病毒扫描启用步骤见 [10.2 上传文件病毒扫描](../guides/operations.md#102-上传文件病毒扫描clamav)。

## 3. H5 前端环境变量

Vite 只暴露 `VITE_` 前缀变量。当前代码实际读取情况：

| 变量 | 是否被读取 | 说明 |
|---|---|---|
| `VITE_API_BASE_URL` | 是 | API 前缀，需包含 `/api`（如 `https://api.example.com/api`）；缺省为 `/api`，开发时走 Vite 代理 |
| `VITE_WS_BASE_URL` | 是 | 默认 `ws://localhost:8000` |
| `VITE_MEDIA_BASE_URL` | 是 | 媒体文件源站，不含 `/media` 前缀，默认 `http://localhost:8000` |
| `VITE_APP_TITLE` / `VITE_APP_DESCRIPTION` | 是 | 应用展示信息 |
| `VITE_JWT_ACCESS_TOKEN_KEY` / `VITE_JWT_REFRESH_TOKEN_KEY` | 否 | 当前 token 存储使用账号槽位 key（`auth_tokens:<userId>`） |

示例（`frontend/.env.development`）：

```env
VITE_API_BASE_URL=/api
VITE_WS_BASE_URL=ws://localhost:8000
VITE_MEDIA_BASE_URL=http://localhost:8000
```

生产环境建议通过 Nginx 将 `/api`、`/ws`、`/media` 反向代理到后端，
这样前端无需感知后端域名。

## 4. 微信小程序环境变量

Uni-app 仅识别 `VUE_APP_` 前缀变量。

| 变量 | 必填 | 说明 |
|---|---|---|
| `VUE_APP_API_BASE_URL` | 是 | 必须包含 `/api`，例如 `https://api.example.com/api` |
| `VUE_APP_WS_BASE_URL` | 是 | 必须包含 `/ws/chat`，代码会追加 `/public` 或 `/private/<id>` |

示例：

```env
VUE_APP_API_BASE_URL=https://api.example.com/api
VUE_APP_WS_BASE_URL=wss://api.example.com/ws/chat
```

生产环境必须使用 HTTPS/WSS，并在微信公众平台配置 request/socket 合法域名。

## 5. Docker Compose 变量

根目录 `.env` 供 `docker-compose.yml` / `docker-compose.prod.yml` 使用：

| 变量 | 用途 |
|---|---|
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | MySQL 容器与 Django |
| `RABBITMQ_USER` / `RABBITMQ_PASSWORD` | RabbitMQ 容器与 Celery |
| `DJANGO_SECRET_KEY` | Django |
| `ALLOWED_HOSTS` | Django |
| `PROD_DOMAIN` | Nginx `server_name` |
| `SSL_CERT_PATH` / `SSL_KEY_PATH` | 容器内证书路径 |
| `SSL_CERT_HOST_PATH` / `SSL_KEY_HOST_PATH` | 宿主机证书挂载路径 |

生产部署完整步骤见 [部署指南](../guides/deployment.md)。

## 6. 配置检查清单

- [ ] `DJANGO_SECRET_KEY` 不是示例值
- [ ] `DJANGO_DEBUG=False`
- [ ] `ALLOWED_HOSTS` 包含真实域名
- [ ] `CORS_ALLOWED_ORIGINS` 只包含可信前端域名
- [ ] 数据库、Redis、RabbitMQ 使用强密码
- [ ] `REDIS_WS_URL` 与 `REDIS_CACHE_URL` 分离
- [ ] `ELASTICSEARCH_HOSTS` 指向可用集群
- [ ] 小程序使用 HTTPS/WSS
- [ ] `.env` 未被提交到版本库
