# 运维手册

本文面向日常运行维护：健康检查、日志、异步任务、搜索索引、缓存、备份与故障处置。
部署步骤见 [部署指南](deployment.md)。

## 1. 健康检查

| 检查项 | 方式 | 预期 |
|---|---|---|
| 后端存活 | `GET /api/health/` | `{"status":"ok"}` |
| 依赖组件 | `GET /api/health/?deep=1` | 全部正常返回 200；任一异常返回 503 与 `components` 明细 |
| 聊天服务 | `GET /api/chat/health/` | 200 |
| 学校服务 | `GET /api/schools/test-connection/` | 200 |
| 前端 | 访问站点首页 | 正常渲染 |
| WebSocket | 连接 `/ws/chat/public/` | 收到 `welcome` / `auth_success` |
| Celery | `celery -A config inspect ping` | `pong` |
| ES | `curl http://localhost:9200/_cluster/health` | `status` 为 green/yellow |

## 2. 日志

| 来源 | 位置 |
|---|---|
| Django 文件日志 | `backend/logs/django.log` |
| 启动脚本日志 | `backend/logs/start_server.log` |
| gunicorn / uvicorn | 标准输出，由 Docker 或 systemd 收集 |
| Nginx | `/var/log/nginx/access.log`、`error.log` |
| Docker | `docker compose logs -f <service>` |

常用命令：

```bash
docker compose logs -f --tail=200 django-http
docker compose logs -f --tail=200 django-ws
docker compose logs -f --tail=200 celery-worker
docker compose logs -f --tail=200 nginx
```

日志级别在 `settings.LOGGING` 中配置；`chat`、`users` 默认 `DEBUG`，
生产环境建议调为 `INFO` 以减少日志量。

## 3. Celery

### 3.1 查看任务与队列

```bash
cd backend
uv run celery -A config inspect active
uv run celery -A config inspect scheduled
uv run celery -A config inspect stats
```

### 3.2 任务清单

| 任务 | 触发时机 |
|---|---|
| `users.tasks.update_user_points_async` | 注册、登录、发帖、评论、点赞、收藏、签到、课程等 |
| `users.tasks.send_notification_async` | 创建通知后，经 `transaction.on_commit` 派发 |
| `search.tasks.index_object` / `remove_object` | 模型保存/删除后同步索引 |

详细参数见 [后台任务参考](../reference/background-jobs.md)。

### 3.3 Flower

Flower 随 Compose 启动，仅绑定本机回环地址：

```bash
docker compose up -d flower
# 浏览器打开 http://127.0.0.1:5555
```

生产环境仅绑定本机回环地址（`127.0.0.1:5555`），通过 SSH 隧道访问：

```bash
ssh -L 5555:127.0.0.1:5555 user@server
```

Flower 同时提供 Prometheus 指标：`http://flower:5555/metrics`。

### 3.4 任务堆积

1. 检查 Worker 是否存活：`docker compose ps celery-worker`
2. 检查 Broker：RabbitMQ 管理台 `15672` 或 Redis
3. 临时扩容：`--concurrency` 或增加 Worker 副本
4. 若大量任务失败，先查看 Worker 日志中的异常堆栈

> 已配置 `CELERY_BEAT_SCHEDULE`：每 10 分钟执行一次 `learning.tasks.send_study_reminders`
> 扫描学习提醒。Compose 中由 `celery-beat` 服务负责调度，排查时先确认该服务运行：
>
> ```bash
> docker compose ps celery-beat
> docker compose logs -f --tail=100 celery-beat
> ```

## 4. Elasticsearch

### 4.1 健康与索引

```bash
curl http://localhost:9200/_cluster/health?pretty
curl http://localhost:9200/_cat/indices?v
```

索引前缀由 `ELASTICSEARCH_INDEX_PREFIX` 决定，默认 `campus`：

- `campus_schools`
- `campus_topics`
- `campus_posts`
- `campus_contents`
- `campus_courses`
- `campus_users`

### 4.2 重建

```bash
cd backend
uv run python manage.py rebuild_search_index --delete
```

重建期间搜索会短暂走 MySQL 降级，属预期行为。

### 4.3 ES 故障

ES 不可用时：

- `search/client.py` 的健康检查返回 false
- `SearchService` 自动降级为 MySQL `LIKE` / `icontains`
- 索引任务直接跳过，不会阻塞业务写入

恢复 ES 后应执行一次全量重建，补齐故障期间的数据。

## 5. 缓存

统一缓存层位于 `core/cache_utils.py`，支持：

- 分层 TTL：`hot` 600s、`medium` 300s、`cold` 3600s
- 空值缓存、互斥锁、随机抖动
- 命名空间版本号失效
- 大 value gzip 压缩
- Redis 异常时降级执行 loader

缓存 key 前缀：`CACHE_KEY_PREFIX`（默认 `campus`）。

手动失效某个命名空间：

```python
from core.cache_utils import bump_cache_version
bump_cache_version('schools')
```

## 6. 数据库

### 6.1 备份

```bash
docker compose exec -T mysql mysqldump \
  -u"$DB_USER" -p"$DB_PASSWORD" \
  --single-transaction --routines --triggers \
  "$DB_NAME" > backup_$(date +%F_%H%M).sql
```

建议：

- 每日全量备份，保留 7–30 天
- 大版本发布前额外备份
- 定期做恢复演练

### 6.2 读写分离

配置 `DB_REPLICA_HOST` 后，读请求走从库。注意：

- 主从延迟会导致“刚写入马上读不到”
- 对一致性敏感的接口应显式使用主库（`using('default')`）
- 未配置从库时自动回退主库

## 7. 实时服务

### 7.1 连接数

生产 Channel Layer 使用 Redis：

- `capacity` 1500
- `expiry` 10s

可通过 Redis 监控或连接数指标观察。在线人数统计基于“最近 5 分钟活跃”，
不是精确连接数，见 `chat/views.py` 中的 `RecentActivePresence`。

### 7.2 横向扩容

- `django-ws` 可启动多个副本，共享同一 Redis Channel Layer
- 私聊组名为 `private_{minId}_{maxId}`，跨进程可正确广播
- 生产 `DEBUG=False` 才能使用 Redis Channel Layer；
  开发环境的 InMemory 层不支持多进程

### 7.3 常见错误码

| 关闭码 | 含义 |
|---|---|
| 4001 | 未认证 |
| 4002 | 缺少目标用户 ID |
| 4003 | 双方不是好友 |
| 4004 | 目标用户不存在 |

## 8. 日常巡检清单

- [ ] 健康检查接口正常
- [ ] Nginx 5xx 比例正常
- [ ] Celery 无大量失败/积压
- [ ] ES 集群状态正常，索引存在
- [ ] Redis 内存与连接数正常
- [ ] MySQL 连接数、慢查询正常
- [ ] 磁盘空间充足（日志、媒体、备份）
- [ ] 证书剩余有效期 > 30 天
- [ ] WebSocket 公网连接正常

## 9. 发布与回滚

发布：

```bash
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

回滚：

1. 切回上一个 Git tag/commit
2. 重新构建并启动
3. 若包含数据库迁移，确认迁移是否可逆；不可逆时使用备份恢复
4. 重建 ES 索引（如模型/文档结构变化）

> 生产迁移遵循“先备份、再迁移、后发布”的顺序。

## 10. 监控（Prometheus + Grafana）

监控栈为可选 profile，不影响默认启动：

```bash
docker compose --profile monitoring up -d
```

生产环境（叠加 `docker-compose.prod.yml`）下 Prometheus、Grafana、Flower
均只绑定 `127.0.0.1`，需通过 SSH 隧道访问，例如：

```bash
ssh -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 user@server
```

| 服务 | 地址 | 说明 |
|---|---|---|
| Prometheus | http://localhost:9090 | 指标抓取与告警规则 |
| Grafana | http://localhost:3000 | 默认账号 `admin`，密码取 `GRAFANA_ADMIN_PASSWORD` |
| Flower | http://127.0.0.1:5555 | Celery 任务/Worker，同时提供 `/metrics` |
| MySQL Exporter | 内部 `mysql-exporter:9104` | 需预先创建监控账号 |
| Redis Exporter | 内部 `redis-exporter-ws:9121`、`redis-exporter-cache:9121` | 两个 Redis 实例 |
| ES Exporter | 内部 `elasticsearch-exporter:9114` | 集群健康与索引指标 |

首次启用前，在 MySQL 中创建只读监控账号：

```sql
CREATE USER 'exporter'@'%' IDENTIFIED BY 'change-me';
GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'%';
FLUSH PRIVILEGES;
```

并在 `.env` 中设置 `MYSQLD_EXPORTER_PASSWORD` 为同一密码。

告警规则位于 `monitoring/prometheus/alerts.yml`：

| 告警 | 触发条件 |
|---|---|
| `ScrapeTargetDown` | 任意抓取目标 2 分钟不可达 |
| `MySQLTooManyConnections` | 连接数 > 100 持续 5 分钟 |
| `MySQLSlowQueries` | 慢查询速率 > 1/s 持续 10 分钟 |
| `RedisMemoryHigh` | 内存使用率 > 85% |
| `ElasticsearchClusterRed` | 集群状态 red |
| `CeleryNoWorkersOnline` | 无在线 Worker |

Grafana 已预置 Prometheus 数据源，可直接导入社区面板：
MySQL `7362`、Redis `763`、Elasticsearch `12436`、Celery `12364`。
