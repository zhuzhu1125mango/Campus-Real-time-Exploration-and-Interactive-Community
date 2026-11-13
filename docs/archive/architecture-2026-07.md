# 架构优化说明

本文档记录项目本阶段完成的主要架构优化，包括搜索、缓存、异步任务、生产加固等内容。

## 1. Elasticsearch 替换 LIKE 搜索

### 1.1 目标

将原本依赖 MySQL `LIKE` 的全局搜索替换为 Elasticsearch，提升搜索速度与中文分词效果；同时保留 MySQL 降级能力，保证 ES 故障时搜索仍然可用。

### 1.2 实现

- **自定义 ES 镜像**：在 `elasticsearch/Dockerfile` 中集成 `analysis-ik` 中文分词插件。
- **文档映射**：`backend/search/documents.py` 定义了学校、论坛主题、帖子、内容、课程、用户六类搜索文档，统一使用 `ik_max_word` 作为分析器、`ik_smart` 作为搜索分析器。
- **搜索服务**：`backend/search/services.py` 封装 `SearchService`，优先调用 ES；当 `es_is_available()` 返回 false 或 ES 查询异常时，自动降级为 MySQL `LIKE`/`icontains` 查询。
- **ES 客户端**：`backend/search/client.py` 提供单例客户端与健康检查。
- **增量同步**：`backend/search/signals.py` 在模型 `post_save`/`post_delete` 时异步触发索引更新任务。
- **索引任务**：`backend/search/tasks.py` 通过 Celery 执行单条文档的索引与删除。
- **全量重建**：`backend/search/management/commands/rebuild_search_index.py` 支持 `--delete` 全量重建索引。

### 1.3 关键配置

```env
ELASTICSEARCH_HOSTS=http://127.0.0.1:9200
ELASTICSEARCH_TIMEOUT=10
ELASTICSEARCH_FALLBACK_TO_DB=True
ELASTICSEARCH_INDEX_PREFIX=campus
```

### 1.4 上线前必做

```bash
docker compose exec django-http uv run python manage.py rebuild_search_index --delete
```

## 2. 缓存策略细化

### 2.1 目标

建立统一、健壮的缓存工具层，解决缓存穿透、击穿、雪崩问题，并在 Redis 异常时平滑降级。

### 2.2 实现

- **统一缓存层**：`backend/core/cache_utils.py` 提供 `cache_get`、`cache_set`、`cached_result`、`cached` 装饰器等 API。
- **分层 TTL**：`config/settings.py` 中 `CACHE_UTILS.CACHE_TIMEOUTS` 定义 `hot`/`medium`/`cold` 三级 TTL。
- **空值缓存**：`cached_result` 在 loader 返回空时缓存短时空值，防止缓存穿透。
- **互斥锁**：使用 `django-redis` 原生 `lock()` 实现分布式锁，防止缓存击穿。
- **随机抖动**：写入缓存时在 TTL 基础上加入 10% 随机抖动，防止缓存雪崩。
- **版本号失效**：`bump_cache_version(namespace)` 可一键失效整个命名空间下的缓存。
- **gzip 压缩**：大 value 自动 gzip 压缩并打标记。
- **异常降级**：所有缓存操作默认启用 `fallback_on_error`，Redis 异常时直接执行 loader，不阻塞业务。

### 2.3 使用示例

```python
from core.cache_utils import cached_result, build_cache_key

def get_hot_schools():
    key = build_cache_key("schools", "hot")
    return cached_result(
        key=key,
        loader=lambda: School.objects.filter(is_active=True)[:10],
        timeout=600,
        namespace="schools",
    )
```

### 2.4 Redis 拆分

生产环境建议将 Redis 拆分为两个实例：

- `REDIS_WS_URL`：Django Channels 的 Channel Layer，仅用于 WebSocket。
- `REDIS_CACHE_URL`：业务缓存、限流、Celery 结果后端。

开发环境未配置时，二者会回退到 `REDIS_URL`。

## 3. 通知/积分业务异步化

### 3.1 目标

将积分计算、通知推送等旁路逻辑从主请求线程中剥离，改为 Celery 异步任务执行，降低接口延迟，提高系统吞吐量。

### 3.2 积分系统

- **统一规则**：`backend/users/points.py` 集中定义 `POINTS_RULES`、`ACTION_DESCRIPTIONS`、`LEVEL_THRESHOLDS`。
- **当前积分规则**：

| 行为 | 积分 |
|------|------|
| register | 10 |
| login | 2 |
| complete_profile | 20 |
| verified | 50 |
| daily_checkin | 5 |
| consecutive_checkin_3 | 5 |
| consecutive_checkin_7 | 10 |
| post | 10 |
| reply | 5 |
| comment | 5 |
| like | 2 |
| liked | 3 |
| favorite | 2 |
| share | 5 |
| create_course | 15 |
| complete_course | 20 |

- **异步任务**：`backend/users/tasks.py` 中的 `update_user_points_async` 通过 `select_for_update` 锁定用户行，原子更新积分与等级。
- **幂等性**：`users/signals.py` 通过检查 `PointsRecord` 是否已存在，避免重复发放一次性积分（如注册、完善资料、身份认证）。
- **触发信号**：`post_save` 信号监听 `User` 与 `UserProfile`，自动触发积分任务。

### 3.3 通知系统

- **统一模型**：所有通知统一使用 `notifications.Notification`，彻底移除 `forum.Notification`。
- **统一入口**：`notifications/notification_sender.py` 提供 `create_notification`、`send_notification_to_user`、`notify_users`、`notify_forum_event` 等封装。
- **异步推送**：`notifications/signals.py` 在 `Notification` 创建后触发 Celery 任务 `send_notification_async`，通过 WebSocket 向用户实时推送。
- **论坛兼容**：`notify_forum_event` 将原论坛通知类型映射到新的通知类型。
- **content_comment 类型**：自本版本起，评论/回复类事件（`content_comment`）独立映射为 `content_comment` 通知类型，与点赞、关注等 `interaction` 类型区分。历史已创建的 `interaction` 类型记录无法与安全区分，因此保持不变，仅后续新增通知按新规则写入。

### 3.4 Celery 配置

- Broker：RabbitMQ（默认），未配置时回退到 Redis 缓存地址。
- Result Backend：Redis 缓存地址。
- 任务序列化：JSON。
- 默认不启用 `task_always_eager`，仅在旧版 Redis（<6.0）或测试需要时开启。

## 4. 数据库读写分离

### 4.1 目标

生产环境通过 MySQL 主从架构分担读压力。

### 4.2 实现

- `backend/config/db_router.py` 实现 `PrimaryReplicaRouter`。
- 读操作自动路由到 `replica` 数据库；写操作路由到 `default` 主库。
- 未配置 `DB_REPLICA_HOST` 时，`replica` 不存在，读请求自动回退到主库。
- 连接池配置 `CONN_MAX_AGE=600` 与 `CONN_HEALTH_CHECKS=True`，减少连接开销。

## 5. 实时通信架构

### 5.1 WebSocket 分离

生产环境将 HTTP API 与 WebSocket 长连接拆分为独立进程：

- `config/asgi_http.py`：仅暴露 Django HTTP 应用，供 gunicorn + uvicorn worker 使用。
- `config/asgi_ws.py`：仅暴露 Channels WebSocket 路由，使用 `TokenAuthMiddleware` 完成 JWT 认证，供 uvicorn 使用。
- 对应启动脚本：`scripts/start_http.sh`、`scripts/start_ws.sh`。

### 5.2 私信分组

私信 WebSocket 使用 `private_{minId}_{maxId}` 命名分组，避免不同会话互相干扰。

## 6. 生产环境加固

### 6.1 Docker Compose 生产覆盖

`docker-compose.prod.yml` 关闭 MySQL、Redis、RabbitMQ、Elasticsearch、Django 等内部服务的端口暴露，仅对外暴露 Nginx 的 80/443。

### 6.2 Nginx HTTPS 配置

`nginx/nginx.prod.conf` 模板提供：

- HTTP 强制跳转 HTTPS。
- HTTPS 服务，支持 HTTP/2。
- `/ws/` 转发到独立 WebSocket 服务。
- 其余请求转发到 HTTP API 服务。
- 安全响应头与 SSL 安全配置。
- 静态资源长期缓存。

### 6.3 SECRET_KEY 校验

`config/settings.py` 启动时检查 `DJANGO_SECRET_KEY` 环境变量，未设置直接抛出 `ImproperlyConfigured`，避免使用默认弱密钥。

### 6.4 其他安全设置

- `CORS_ALLOW_ALL_ORIGINS = False`
- Cookie Secure/HttpOnly/SameSite
- CSRF 与 Session Cookie 安全设置
- H5 `v-html` 必须使用 `frontend/src/utils/xss.ts` 过滤

## 7. 前端优化

### 7.1 构建产物拆包

`frontend/vite.config.ts` 配置 `manualChunks`，将以下依赖拆分为独立 chunk：

- echarts
- element-plus
- @element-plus/icons-vue
- leaflet
- @vueuse
- axios、pinia、vue-router
- tinymce

### 7.2 ECharts 按需引入

`frontend/src/utils/echarts.ts` 仅注册项目使用的图表类型与组件，避免全量引入。

### 7.3 效果

- 消除了 "Some chunks are larger than 500 kB after minification" 警告。
- Dashboard 与首页 chunk 体积显著下降。

## 8. 已移除的废弃内容

- `forum.Notification` 模型、Admin 注册、相关迁移已彻底移除。
- `backend/start_production.sh` 已删除，统一使用 `scripts/` 下的生产启动脚本。

## 9. 后续建议

1. **Elasticsearch 监控**：生产环境建议增加 ES 集群健康监控与告警。
2. **缓存命中率监控**：可通过 Redis INFO 或 APM 工具观察缓存效果。
3. **Celery 监控**：建议接入 Flower 或类似工具监控任务队列。
4. **日志聚合**：生产环境建议接入 ELK 或 Loki 进行日志收集与分析。
5. **小程序功能补齐**：按计划完成 Content 投稿状态管理、课时播放器增强、全局搜索页。
