# 开发指南

本文面向需要修改代码的开发者，说明项目结构、已有约定和扩展方式。
接口事实见 [API 参考](../reference/api/README.md)，设计原因见 [架构文档](../architecture/overview.md)。

## 1. 仓库结构

```text
.
├── backend/                 # Django 后端
│   ├── config/              # settings / urls / asgi / celery / db_router
│   ├── core/                # 通用 ViewSet 基类、缓存工具、HTML 清洗
│   ├── users/               # 用户、资料、验证码、积分、关注
│   ├── forum/               # 论坛分类/板块/主题/帖子/评论/标签/书签
│   ├── schools/             # 院校、专业、分数线、活动、地点打卡、统计、推荐
│   ├── learning/            # 课程、章节、课时、报名、进度、评价、资源
│   ├── content/             # 内容类型/分类/标签/文章/评论/修订
│   ├── chat/                # 公共聊天室 REST + WebSocket 消费者
│   ├── private_messages/    # 私信 REST（WebSocket 消费者位于 chat）
│   ├── notifications/       # 统一通知模型、发送入口、序列化器
│   ├── activities/          # 用户动态、动态点赞/评论
│   ├── favorites/           # 通用收藏（ContentType 多态）
│   ├── friendships/         # 好友请求、好友关系
│   ├── feed/                # 聚合 Feed、热门话题
│   ├── search/              # ES 文档、客户端、服务、信号、任务、重建命令
│   ├── tests/               # 跨模块单元测试与集成脚本
│   └── scripts/             # 生产启动与初始化脚本
├── frontend/                # Vue 3 H5
│   └── src/{api,components,composables,router,services,stores,types,utils,views}
├── mp-weixin/               # Uni-app 微信小程序
│   ├── api/                 # 请求封装与各业务 API
│   ├── pages/               # 27 个页面
│   └── utils/               # 日期、图片、XSS 等工具
├── shared/                  # 三端共享的常量与工具（H5/小程序）
├── nginx/                   # 开发与生产 Nginx 配置
├── elasticsearch/           # 内置 ik 分词的 ES 镜像
├── docker-compose.yml       # 基础编排
├── docker-compose.prod.yml  # 生产覆盖
└── docs/                    # 文档中心
```

## 2. 后端开发约定

### 2.1 分层

```text
urls.py / DRF Router
        ↓
views.py（ViewSet / APIView）
        ↓
serializers.py（校验与输出）
        ↓
models.py（持久化）
        ↕
signals.py / tasks.py（异步副作用）
```

- **业务逻辑优先放在 ViewSet 的 action 或 app 内的 `services/`**，
  不要把跨模型事务写进 serializer。
- `schools/services/` 存放板块创建等可复用服务；`schools/recommendation.py`、`schools/stats.py`
  分别负责推荐与统计。
- 跨 app 的通知统一调用 `notifications.notification_sender`，不要直接创建 `Notification`。

### 2.2 ViewSet 基类

所有 ViewSet 优先继承 `core/base_viewsets.py`：

| 基类 | 用途 |
|---|---|
| `BaseModelViewSet` | 通用 CRUD，支持配置化权限/限流/查询优化 |
| `PublicReadOnlyModelViewSet` | 读公开、写需登录（论坛、内容、课程等） |
| `AuthenticatedModelViewSet` | 所有操作需登录 |
| `AdminModelViewSet` | 管理员专用 |

通过类属性声明策略，避免在每个 action 里手写 if/else：

```python
class TopicViewSet(PublicReadOnlyModelViewSet):
    serializer_class = TopicListSerializer
    select_related_fields = ['author', 'board']
    prefetch_related_fields = ['tags']
    permission_config = {
        'list': [permissions.AllowAny],
        'create': [permissions.IsAuthenticated],
        'close': [permissions.IsAuthenticated, IsOwnerOrAdmin],
    }
    throttle_config = {
        'list': [SearchThrottle],
        'create': [WriteThrottle],
    }
```

新增 action 时：

1. 用 `@action(detail=..., methods=[...])` 声明路由。
2. 在 `permission_config` 中显式配置权限；未配置时回退到基类默认值。
3. 写操作在 `throttle_config` 中绑定 `WriteThrottle`。
4. 涉及关联对象读取时，补充 `select_related_fields` / `prefetch_related_fields`，避免 N+1。

### 2.3 认证、权限、限流

- 认证：JWT（`Authorization: Bearer <access>`）+ Session；access 30 分钟，refresh 1 天，
  开启轮换与黑名单。
- 权限：`IsAuthenticated`、`IsAdminUser`、`IsOwnerOrAdmin`（`users/permissions.py`）。
- 限流：`users/throttles.py` 提供 `SearchThrottle`、`WriteThrottle`；
  全局限流在 `settings.REST_FRAMEWORK.DEFAULT_THROTTLE_RATES`。

### 2.4 富文本与 XSS

用户可输入的 HTML 字段必须在入库前清洗：

```python
from core.html_sanitizer import sanitize_html

def save(self, *args, **kwargs):
    self.content = sanitize_html(self.content)
    super().save(*args, **kwargs)
```

已覆盖：`User.bio`、论坛 `Post.content` / `Comment.content`、内容 `Content.content` /
`Content.summary` / 评论 / 修订、WebSocket 聊天消息。新增富文本字段时不要遗漏。

### 2.5 异步任务与事务

积分、通知、搜索索引都是 Celery 任务。必须遵守：

```python
# 正确：事务提交后再派发
from users.tasks import queue_update_user_points
queue_update_user_points(user.id, 'post')

# 不要在新代码中直接调用
# update_user_points_async.delay(...)
```

- 在事务中创建通知后，推送任务通过 `transaction.on_commit` 延迟派发（已由 `notifications/signals.py` 处理）。
- 一次性积分（注册、完善资料、认证）通过 `PointsRecord` 幂等检查，避免重复发放。
- 任务本身需要可重试、可幂等；失败会按 `max_retries=3` 重试。

### 2.6 数据库与迁移

```bash
cd backend
uv run python manage.py makemigrations <app>
uv run python manage.py migrate
uv run python manage.py makemigrations --check --dry-run   # CI/提交前检查
```

- 新增模型字段时同步检查：序列化器、Admin、搜索文档、索引信号、前端类型。
- 大表加索引优先在模型 `Meta.indexes` 中声明，命名保持 `<app>_<table>_<cols>_idx` 风格。
- 生产迁移由 `scripts/init_django.sh` 或独立 `django-init` 服务执行一次，
  不要在每个 HTTP 实例启动时执行。

### 2.7 新增一个业务接口的检查清单

- [ ] 模型字段与迁移
- [ ] serializer（读/写分离，必要时做字段级校验）
- [ ] ViewSet + `@action`，配置权限与限流
- [ ] URL 注册（app `urls.py` 或 Router）
- [ ] 查询优化（`select_related` / `prefetch_related` / `annotate`）
- [ ] 副作用：积分、通知、搜索索引是否触发
- [ ] 单元测试
- [ ] API 参考文档与数据模型文档

## 3. H5 前端约定

### 3.1 目录职责

| 目录 | 职责 |
|---|---|
| `api/` | 按业务域封装请求，不在组件里直接拼 URL |
| `views/` | 路由页面 |
| `components/` | 可复用组件（含 `common/` 基础组件） |
| `stores/` | Pinia：`authStore`、`tokenStore`、`userProfileStore`、`userStore`（聚合） |
| `utils/request.ts` | Axios 实例、JWT 注入、并发刷新、CSRF |
| `utils/xss.ts` | `v-html` 渲染前的清洗 |
| `types/` | 与后端响应对应的 TypeScript 类型 |

### 3.2 请求与登录态

- 统一使用 `utils/request.ts`，响应拦截器已返回 `response.data`。
- Token 按账号槽位存储：`auth_tokens:<userId>`，支持多账号切换。
- 401 时只允许一个刷新请求，其余并发请求复用同一个 `refreshPromise`。
- 新增 API 时先在 `api/<domain>.ts` 中封装，再在页面中调用。

### 3.3 路由与权限

- 路由集中在 `src/router/index.ts`，需要登录的页面标注 `meta: { requiresAuth: true }`。
- 路由守卫只判断本地 token 是否存在，并在后台触发用户信息加载；
  真正的权限由后端接口返回 401/403 决定。

### 3.4 UI 与样式

- UI 组件：Element Plus + `radix-vue` + 自定义 `components/common/`。
- 样式：UnoCSS + 原生 CSS；不要在模板中堆叠大量行内样式。
- 富文本渲染必须经过 `xss.ts`，不要直接 `v-html`。

### 3.5 构建

```bash
cd frontend
pnpm type-check
pnpm build
```

`vite.config.ts` 使用 `manualChunks` 拆分 echarts、element-plus、leaflet、vueuse 等大依赖。

## 4. 微信小程序约定

- 页面位于 `mp-weixin/pages/<feature>/`，路由在 `pages.json` 注册。
- 请求统一使用 `mp-weixin/api/request.js`：自动注入 Bearer token、401 刷新、重试。
- WebSocket 使用 `getWebSocketUrl(path)` 与 `getWebSocketProtocols()`：
  - 公共聊天：`getWebSocketUrl('public')`
  - 私聊：`getWebSocketUrl('private/<userId>')`
  - token 通过 `jwt` 子协议传递，不放在 URL。
- 环境变量只识别 `VUE_APP_*`，不得硬编码内网 IP。
- 新增页面时同步检查：`pages.json`、入口跳转、登录态、错误提示、生命周期清理（定时器/WS）。

## 5. 共享代码

`shared/` 存放 H5 与小程序共用的纯函数与常量：

- `shared/constants/api.js`
- `shared/utils/date.js`
- `shared/utils/image.js`
- `shared/utils/xss.js`

修改共享代码后必须同时验证 H5 与小程序两端，避免只在一端通过类型检查。

## 6. 依赖与提交

- 后端：`uv add <pkg>`，提交 `pyproject.toml` 与 `uv.lock`。
- 前端：`pnpm add <pkg>`，提交 `package.json` 与 `pnpm-lock.yaml`；不要提交 `package-lock.json` / `yarn.lock`。
- 提交前执行：
  ```bash
  cd backend && uv run python manage.py check
  cd backend && uv run python manage.py makemigrations --check --dry-run
  cd frontend && pnpm type-check
  ```
- 提交规范与评审清单见 [贡献指南](../project/contributing.md)。
