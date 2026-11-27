# 后台任务参考

## 1. 任务注册

`config/celery.py` 会遍历 `INSTALLED_APPS` 并导入每个 app 的 `tasks.py`。
新增任务时：

1. 在 app 下创建/编辑 `tasks.py`
2. 使用 `@shared_task(bind=True, max_retries=..., default_retry_delay=...)`
3. 在任务内部延迟导入模型，避免 app 加载顺序问题
4. 必须可重试、可幂等

## 2. 任务清单

### 2.1 积分更新

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def update_user_points_async(self, user_id, action, description=None, extra_points=None)
```

| 项 | 说明 |
|---|---|
| 触发 | 注册、登录、发帖、回复、评论、点赞、被点赞、收藏、签到、创建/完成课程 |
| 幂等 | 一次性行为通过 `PointsRecord` 查重 |
| 并发 | `select_for_update` 锁定用户行 |
| 失败 | 自动重试 3 次 |

统一通过 `queue_update_user_points(user_id, action, ...)` 派发；
该函数在事务中会使用 `transaction.on_commit`。

### 2.2 通知推送

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def send_notification_async(self, notification_id)
```

| 项 | 说明 |
|---|---|
| 触发 | `Notification.post_save` 信号，经 `transaction.on_commit` |
| 行为 | 查询通知 → 推送 `notification` → 推送未读数 |
| 目标组 | `user_<recipient_id>` |
| 失败 | 通知不存在则跳过；其他异常重试 |

### 2.3 搜索索引

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def index_object(self, app_label_model, object_id)

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def remove_object_from_index(self, app_label_model, object_id)
```

| 项 | 说明 |
|---|---|
| 触发 | `School`、`Topic`、`Post`、`Content`、`Course`、`User` 的 `post_save` / `post_delete` |
| 参数 | `app_label_model` 形如 `schools.School` |
| ES 不可用 | 直接返回，不重试 |
| 失败 | ES 写入异常时重试 |

## 3. 积分规则

`users/points.py`：

| action | 积分 | 说明 |
|---|---|---|
| `register` | 10 | 注册奖励 |
| `login` | 2 | 每日首次登录 |
| `complete_profile` | 20 | 完善资料 |
| `verified` | 50 | 身份认证 |
| `daily_checkin` | 5 | 每日签到 |
| `consecutive_checkin_3` | 5 | 连续 3 天额外 |
| `consecutive_checkin_7` | 10 | 连续 7 天额外 |
| `post` | 10 | 发帖 |
| `reply` | 5 | 回复 |
| `comment` | 5 | 评论 |
| `like` | 2 | 点赞 |
| `liked` | 3 | 被点赞 |
| `favorite` | 2 | 收藏 |
| `share` | 5 | 分享 |
| `create_course` | 15 | 创建课程 |
| `complete_course` | 20 | 完成课程 |
| `system` | 0 | 系统奖励 |
| `admin` | 0 | 管理员操作 |

等级阈值：

```python
LEVEL_THRESHOLDS = [0, 50, 200, 500, 1000, 2000, 5000, 10000]
```

等级名称：新手、初级学员、中级学员、高级学员、学霸、学神、导师、大师。

## 4. 通知类型

| 类型 | 触发示例 |
|---|---|
| `system` | 系统公告、管理员发送 |
| `interaction` | 好友请求、点赞、关注 |
| `content_comment` | 评论/回复内容 |
| `message` | 私信 |
| `activity` | 活动相关 |

## 5. 搜索索引

| 文档 | 索引 | 数据源 |
|---|---|---|
| `SchoolDocument` | `campus_schools` | `School` |
| `TopicDocument` | `campus_topics` | `Topic` |
| `PostDocument` | `campus_posts` | `Post` |
| `ContentDocument` | `campus_contents` | `Content` |
| `CourseDocument` | `campus_courses` | `Course` |
| `UserDocument` | `campus_users` | `User` |

索引名随 `ELASTICSEARCH_INDEX_PREFIX` 变化。

## 6. 缓存任务

缓存不在 Celery 中执行，但以下操作会触发缓存失效：

- `bump_cache_version(namespace)`：命名空间版本号 +1
- 数据变更后由视图显式失效对应 key
- TTL 到期自然失效

## 7. 手动执行

```bash
cd backend

# 同步执行一个任务（调试）
uv run python manage.py shell
>>> from users.tasks import update_user_points_async
>>> update_user_points_async(1, 'post')

# 查看注册任务
uv run celery -A config inspect registered

# 全量重建索引
uv run python manage.py rebuild_search_index --delete

# 清理未被内容引用的富文本图片（默认 7 天前）
uv run python manage.py cleanup_content_images --days 7 --dry-run
uv run python manage.py cleanup_content_images --days 7
```

## 8. 定时任务

`settings.py` 已配置 Beat 调度：

```python
CELERY_BEAT_SCHEDULE = {
    'send-study-reminders': {
        'task': 'learning.tasks.send_study_reminders',
        'schedule': 600.0,  # 每 10 分钟
    },
}
```

| 任务 | 说明 |
|---|---|
| `learning.tasks.send_study_reminders` | 扫描到期的学习提醒，向未完成课程的用户发送站内通知；同一提醒每天最多一次 |

启动方式：

```bash
# 本地
cd backend
uv run celery -A config beat --loglevel info

# Compose（已包含 celery-beat 服务）
docker compose up -d celery-beat
```

新增周期任务时，请同时补充任务实现与测试，再加入 `CELERY_BEAT_SCHEDULE`。

## 9. 失败排查

| 现象 | 排查 |
|---|---|
| 任务不执行 | Worker、Broker、eager 配置 |
| 积分不增加 | `PointsRecord` 是否已存在、用户是否存在、action 是否在规则表 |
| 通知不推送 | 通知是否存在、`transaction.on_commit` 是否执行、Channel Layer 是否可用 |
| 索引不更新 | ES 是否可用、任务是否进入队列、`app_label_model` 是否正确 |
| 任务重复 | 检查是否绕过 `queue_update_user_points`、是否缺少幂等判断 |
