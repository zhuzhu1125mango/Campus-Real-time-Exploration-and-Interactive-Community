# 异步、搜索与缓存

本文解释三条旁路能力：Celery 异步任务、Elasticsearch 搜索、统一缓存层。

## 1. Celery 异步任务

### 1.1 配置

`config/celery.py`：

- 从 Django settings 读取 `CELERY_*` 配置
- 显式遍历 `INSTALLED_APPS` 导入各 app 的 `tasks.py`，避免自动发现失败
- Broker 默认 RabbitMQ，未配置时回退 Redis
- 结果后端使用 Redis Cache

任务默认：

| 项 | 值 |
|---|---|
| 序列化 | JSON |
| 单任务时限 | 30 分钟 |
| 预取倍数 | 1 |
| 重试 | 最多 3 次，间隔 5 秒（按任务声明） |
| eager 模式 | 默认关闭 |

### 1.2 任务清单

| 任务 | 参数 | 触发 |
|---|---|---|
| `users.tasks.update_user_points_async` | `user_id, action, description=None, extra_points=None` | 各类业务行为 |
| `users.tasks.send_notification_async` | `notification_id` | 通知创建后 |
| `search.tasks.index_object` | `app_label_model, object_id` | 模型 `post_save` |
| `search.tasks.remove_object_from_index` | `app_label_model, object_id` | 模型 `post_delete` |

### 1.3 事务协作

核心规则：**任务必须在事务提交后派发**。

```python
def queue_update_user_points(user_id, action, description=None, extra_points=None):
    def _dispatch():
        update_user_points_async.delay(user_id, action, **kwargs)

    if transaction.get_connection().in_atomic_block:
        transaction.on_commit(_dispatch)
    else:
        _dispatch()
```

通知同理：`notifications/signals.py` 在 `post_save` 中使用 `transaction.on_commit`。

原因：若在事务内立即派发，Worker 可能在数据提交前读取，导致：

- 查不到通知记录
- 读到旧积分
- 事务回滚后任务仍执行

### 1.4 幂等

- 一次性积分：查询 `PointsRecord` 是否已存在。
- 每日签到：锁定用户行 + 当天记录，防止并发重复。
- 连续签到奖励：按当天是否已发放判断。
- 通知推送：按 `notification_id` 查询，不存在则跳过。

## 2. 积分系统

积分规则统一在 `users/points.py`：

| 行为 | 积分 |
|---|---|
| 注册 `register` | 10 |
| 每日登录 `login` | 2 |
| 完善资料 `complete_profile` | 20 |
| 身份认证 `verified` | 50 |
| 每日签到 `daily_checkin` | 5 |
| 连续签到 3 天 | +5 |
| 连续签到 7 天 | +10 |
| 发帖 `post` | 10 |
| 回复 `reply` | 5 |
| 评论 `comment` | 5 |
| 点赞 `like` | 2 |
| 被点赞 `liked` | 3 |
| 收藏 `favorite` | 2 |
| 分享 `share` | 5 |
| 创建课程 `create_course` | 15 |
| 完成课程 `complete_course` | 20 |
| 系统奖励 `system` | 0 |
| 管理员操作 `admin` | 0 |

等级阈值：

| 等级 | 名称 | 累计积分 |
|---|---|---|
| 1 | 新手 | 0 |
| 2 | 初级学员 | 50 |
| 3 | 中级学员 | 200 |
| 4 | 高级学员 | 500 |
| 5 | 学霸 | 1000 |
| 6 | 学神 | 2000 |
| 7 | 导师 | 5000 |
| 8 | 大师 | 10000 |

更新方式：`select_for_update` 锁行 → 写 `PointsRecord` → 原子更新 `points`/`level`。

## 3. 通知系统

### 3.1 模型

统一使用 `notifications.Notification`，表名 `users_notification`。

| 字段 | 说明 |
|---|---|
| `recipient` | 接收者 |
| `sender` | 发送者，可空 |
| `notification_type` | 类型 |
| `title` / `content` | 展示内容 |
| `content_type` / `object_id` / `related_object` | 通用关联 |
| `url` | 点击跳转 |
| `is_read` | 已读状态 |

### 3.2 类型

| 类型 | 用途 |
|---|---|
| `system` | 系统通知 |
| `interaction` | 点赞、关注等互动 |
| `content_comment` | 评论/回复 |
| `message` | 私信 |
| `activity` | 活动通知 |

> 历史评论通知可能仍为 `interaction`，从当前版本起新评论使用 `content_comment`。

### 3.3 发送入口

统一使用 `notifications/notification_sender.py`：

- `create_notification(...)`
- `send_notification_to_user(...)`
- `notify_users(...)`
- `notify_forum_event(...)`

不要直接 `Notification.objects.create`，否则会绕过统一字段与后续扩展。

### 3.4 推送链路

```text
create_notification
  → Notification.post_save
  → transaction.on_commit
  → send_notification_async.delay(id)
  → WebSocket group user_<recipient_id>
  → 客户端收到 notification + unread_notifications
```

## 4. Elasticsearch 搜索

### 4.1 索引

`search/documents.py` 定义 6 类文档，索引名带前缀：

| 文档 | 索引 | 主要字段 |
|---|---|---|
| `SchoolDocument` | `campus_schools` | name、english_name、abbreviation、province、city、type、level |
| `TopicDocument` | `campus_topics` | title、content、author、board、tags、status |
| `PostDocument` | `campus_posts` | content、topic_title、author |
| `ContentDocument` | `campus_contents` | title、summary、content、author、tags |
| `CourseDocument` | `campus_courses` | title、description、instructor、category |
| `UserDocument` | `campus_users` | username、bio、school、major |

中文分词：

- 建索引：`ik_max_word`
- 搜索：`ik_smart`

### 4.2 查询

`search/services.py` 的 `SearchService`：

1. `es_is_available()` 健康检查
2. ES 可用：`multi_match` 查询，取 `hit.meta.id` 后回表 ORM
3. ES 失败或不可用：按 `ELASTICSEARCH_FALLBACK_TO_DB` 决定是否降级
4. 降级：`icontains` / `Q` 组合查询

空查询直接返回空结果，避免全表扫描。

### 4.3 同步

- `search/signals.py` 监听 School、Topic、Post、Content、Course、User 的保存/删除
- 保存 → `index_object.delay(...)`
- 删除 → `remove_object_from_index.delay(...)`
- ES 不可用时任务直接返回，不阻塞业务

### 4.4 重建

```bash
cd backend
uv run python manage.py rebuild_search_index --delete
uv run python manage.py rebuild_search_index --model schools.School --delete
```

生产由 `django-init` 执行一次。

### 4.5 降级行为

| 场景 | 行为 |
|---|---|
| ES 未启动 | 全部走 MySQL LIKE |
| ES 查询异常 | 记录 warning，走 MySQL |
| ES 索引为空 | 查询无结果，学校列表会回退 LIKE |
| 索引任务失败 | 业务不受影响，索引可能滞后 |

## 5. 缓存

### 5.1 后端

| 环境 | 后端 |
|---|---|
| `DEBUG=True` | LocMemCache |
| `DEBUG=False` | django-redis + `REDIS_CACHE_URL` |

`core/cache_utils.py` 提供：

| 能力 | 说明 |
|---|---|
| 分层 TTL | hot 600s / medium 300s / cold 3600s |
| 空值缓存 | loader 返回空时写短 TTL 哨兵，防穿透 |
| 互斥锁 | django-redis `lock()`，防击穿 |
| 随机抖动 | TTL 加 10% 抖动，防雪崩 |
| 版本号失效 | `bump_cache_version(namespace)` |
| gzip | 大 value 自动压缩 |
| 异常降级 | Redis 异常直接执行 loader |

缓存 key 由 `build_cache_key` / `build_query_cache_key` 生成，统一带前缀与命名空间。

### 5.2 缓存对象

缓存**序列化后的数据**，不要缓存 QuerySet：

```python
result = cached_result(
    key=build_query_cache_key('schools', 'list', request.query_params.urlencode()),
    loader=lambda: serialize(page),
    timeout=get_default_timeout('hot'),
    namespace='schools',
)
```

### 5.3 Redis 拆分

| 实例 | 用途 | 变量 |
|---|---|---|
| Redis WS | Channel Layer | `REDIS_WS_URL` |
| Redis Cache | 业务缓存、限流、Celery 结果 | `REDIS_CACHE_URL` |

拆分原因：WebSocket 广播是高频、短 TTL 的写入，业务缓存是低频、较大 value 的读写；
混用会互相影响内存与延迟。

## 6. 故障与可观测性

| 故障 | 影响 | 处理 |
|---|---|---|
| Worker 停止 | 积分/通知/索引延迟 | 重启 Worker，检查 Broker |
| RabbitMQ 不可用 | 任务无法投递 | 恢复 RabbitMQ 或临时切换 Redis |
| ES 不可用 | 搜索降级 | 恢复 ES 后全量重建索引 |
| Redis Cache 不可用 | 缓存失效，回源数据库 | 检查 Redis Cache 实例 |
| Redis WS 不可用 | WebSocket 无法跨进程广播 | 检查 Redis WS 与 Channel Layer |
| 缓存 key 版本未更新 | 读到旧数据 | `bump_cache_version(namespace)` |

日常巡检见 [运维手册](../guides/operations.md)，任务明细见
[后台任务参考](../reference/background-jobs.md)。
