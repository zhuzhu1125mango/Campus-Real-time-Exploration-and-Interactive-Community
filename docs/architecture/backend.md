# 后端架构

后端是 Django 6 + DRF 的模块化单体，按业务域拆分 app，通过统一的 ViewSet 基类、
通知入口和异步任务层保持一致性。

## 1. App 划分

| App | 职责 | 主要模型 |
|---|---|---|
| `users` | 自定义用户、资料、验证码、积分、关注、管理员入口 | `User`、`UserProfile`、`VerificationCode`、`UserActivity`、`PointsRecord` |
| `forum` | 论坛分类/板块/主题/帖子/评论/标签/书签/举报 | `Category`、`Board`、`Topic`、`Post`、`Comment`、`Tag`、`Bookmark`、`Report` |
| `schools` | 院校、专业、分数线、活动、地点打卡、推荐、统计 | `School`、`Major`、`SchoolMajor`、`AdmissionScore`、`Event`、`Place`、`CheckIn` |
| `learning` | 课程、章节、课时、报名、进度、评价、资源 | `Course`、`Chapter`、`Lesson`、`Enrollment`、`Progress`、`Review` |
| `content` | 内容类型/分类/标签/文章/评论/修订 | `ContentType`、`Content`、`Comment`、`ContentRevision` |
| `chat` | 公共聊天室 REST 与 WebSocket | `ChatMessage` |
| `private_messages` | 私信 REST | `Message` |
| `notifications` | 统一通知模型与发送入口 | `Notification` |
| `activities` | 用户动态、动态点赞/评论 | `Activity`、`ActivityLike`、`ActivityComment` |
| `favorites` | 通用收藏（多态） | `Favorite` |
| `friendships` | 好友请求与好友关系 | `FriendRequest`、`Friend` |
| `feed` | 聚合 Feed、热门话题 | 无自有模型 |
| `search` | ES 文档、查询服务、信号、任务 | 无自有模型 |
| `core` | ViewSet 基类、缓存工具、HTML 清洗 | 无 |
| `config` | 设置、路由、ASGI、Celery、数据库路由 | 无 |

依赖方向尽量保持「业务 app → core / notifications / users」，
避免 app 之间互相直接导入视图。

## 2. 分层与请求生命周期

```text
config/urls.py
  └─ <app>/urls.py（DRF Router）
       └─ ViewSet
            ├─ get_permissions()  ← permission_config
            ├─ get_throttles()    ← throttle_config
            ├─ get_queryset()     ← select_related / prefetch_related / annotate
            ├─ Serializer
            └─ Model / Service
```

### 2.1 ViewSet 基类

`core/base_viewsets.py` 用配置化方式统一权限、限流与查询优化：

```python
class BaseModelViewSet(viewsets.ModelViewSet):
    permission_config = {...}   # action -> [PermissionClass]
    throttle_config = {...}     # action -> [ThrottleClass]
    select_related_fields = []
    prefetch_related_fields = []
    annotation_fields = {}
```

好处：

- 新增 action 时不必重复写 `get_permissions`。
- 列表/详情默认继承同一套查询优化。
- 未在 `permission_config` 中声明的 action 回退到基类默认策略。

### 2.2 分页

存在两套分页配置：

| 场景 | 分页类 | 默认页大小 |
|---|---|---|
| DRF 全局默认 | `PageNumberPagination` | 12 |
| 继承 `BaseModelViewSet` | `StandardResultsSetPagination` | 10 |

两者都支持 `page_size` 查询参数（后者上限 100）。新增接口时应明确使用哪一套，
避免前端对页大小产生错误预期。

## 3. 认证与权限

### 3.1 认证

```python
DEFAULT_AUTHENTICATION_CLASSES = (
    'rest_framework_simplejwt.authentication.JWTAuthentication',
    'rest_framework.authentication.SessionAuthentication',
)
```

JWT 配置：

| 项 | 值 |
|---|---|
| access 有效期 | 30 分钟 |
| refresh 有效期 | 1 天 |
| 轮换 | 开启 |
| 轮换后拉黑旧 refresh | 开启 |
| 请求头 | `Authorization: Bearer <token>` |

登录接口：`POST /api/users/users/login/`，返回 `access`、`refresh`、`user`。
登出接口会把 refresh token 加入黑名单。

### 3.2 权限

- `permissions.IsAuthenticated`
- `permissions.IsAdminUser`
- `users.permissions.IsOwnerOrAdmin`
- 自定义：`IsInstructorOrAdmin`（课程）

公开读取的模块（学校、论坛、内容、课程）使用 `IsAuthenticatedOrReadOnly`
或 `PublicReadOnlyModelViewSet`。

### 3.3 限流

全局限流：

| 范围 | 速率 |
|---|---|
| 匿名 | 60/min |
| 用户 | 120/min |
| 登录 | 10/min |
| 验证码 | 3/min |
| 搜索 | 30/min |
| 写操作 | 60/min |

ViewSet 内通过 `SearchThrottle` / `WriteThrottle` 绑定到具体 action。

## 4. 数据访问与性能

### 4.1 N+1 处理

- 模型层：为高频过滤/排序字段声明 `Meta.indexes`。
- 查询层：`select_related_fields`（外键）、`prefetch_related_fields`（多对多/反向外键）。
- 列表层：论坛主题使用 `Subquery` / `Count(distinct=True)` 注入帖子数与最后回复。

### 4.2 缓存

热点只读数据通过 `core/cache_utils.cached_result` 缓存序列化后的数据，
避免缓存 QuerySet。学校列表是典型例子。

### 4.3 读写分离

`config/db_router.py`：

- `db_for_read` → `replica`（存在时）
- `db_for_write` → `default`
- 迁移/关系读取 → `default`

未配置 `DB_REPLICA_HOST` 时不存在 `replica`，所有请求走主库。

## 5. 模型与数据一致性

### 5.1 富文本清洗

在模型 `save()` 中统一清洗：

- `users.User.bio`
- `forum.Post.content`、`forum.Comment.content`
- `content.Content.content/summary`、`content.Comment.content_text`、`ContentRevision.content_text`

使用 `core/html_sanitizer.sanitize_html`（bleach 白名单）。

### 5.2 事务

- 签到使用 `select_for_update` 锁定用户行，防止并发重复签到。
- 积分任务在事务提交后派发。
- 通知推送在事务提交后派发，避免 Worker 读不到记录。

### 5.3 幂等

一次性积分（注册、完善资料、认证）通过查询 `PointsRecord` 是否已存在来保证幂等。
连续签到奖励按“当天是否已发放”判断。

## 6. 信号与异步

| 信号 | 作用 |
|---|---|
| `users/signals.py` | 注册/资料完善触发积分；等级计算 |
| `forum/signals.py` | 主题/帖子变更触发积分、通知、搜索索引 |
| `notifications/signals.py` | 通知创建后延迟推送 |
| `search/signals.py` | 模型保存/删除后更新 ES |

异步任务统一使用 Celery，详见 [后台任务参考](../reference/background-jobs.md)。

## 7. 错误处理

- DRF 标准异常返回 4xx/5xx JSON。
- 视图内业务错误返回 `{"detail": "..."}` 或 `{"error": "..."}`。
- 全局异常不会被吞掉；生产环境由 Django 日志记录。
- 前端请求层对 400/401/403/404/500 做统一提示。

## 8. 管理后台

Django Admin 承载：

- 用户与积分
- 论坛内容审核
- 学校/专业/分数线/活动
- 课程/课时
- 内容审核

注册入口在各 app 的 `admin.py`。

## 9. 已知技术债

- 部分 app（activities/content/favorites/friendships/private_messages）测试为空。
- 分页存在两套默认值，前端需按接口确认。
- `settings.py` 中部分配置（`SMS_ENABLED`、`MEDIA_URL`）未走环境变量。
- 通知消费者事件名与下发 `type` 不完全一致，协议测试待补充。
