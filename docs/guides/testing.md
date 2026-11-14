# 测试指南

## 1. 测试分层

| 层级 | 位置 | 说明 |
|---|---|---|
| 单元/接口测试 | `backend/<app>/tests.py` | Django `TestCase` + DRF `APIClient` |
| 模块测试 | `backend/schools/tests/` | 学校 API 与扩展场景 |
| 跨模块测试 | `backend/tests/test_points_notifications.py` | 积分、通知、Celery 协作 |
| 集成脚本 | `backend/tests/integration/` | 需要先启动后端，使用真实 HTTP/WS |
| 前端类型检查 | `frontend/` | `vue-tsc --noEmit` |
| 前端 E2E | 暂无自动化 | 手动或后续引入 Playwright |

当前测试文件：

| 文件 | 覆盖范围 | 状态 |
|---|---|---|
| `backend/users/tests.py` | 用户、认证、关注 | 已覆盖 |
| `backend/forum/tests.py` | 论坛主题/帖子/评论 | 已覆盖 |
| `backend/chat/tests.py` | 公共聊天 REST/WS 基础 | 已覆盖 |
| `backend/learning/tests.py` | 课程、报名、进度 | 已覆盖 |
| `backend/feed/tests.py` | Feed 聚合 | 已覆盖 |
| `backend/search/tests.py` | ES 降级、空查询、索引任务 | 已覆盖 |
| `backend/notifications/tests.py` | 通知创建与 WS 推送 | 已覆盖 |
| `backend/schools/tests/` | 学校、推荐、活动、统计 | 已覆盖 |
| `backend/tests/test_points_notifications.py` | 积分规则与异步任务 | 已覆盖 |
| `activities/content/favorites/friendships/private_messages` | — | 测试文件为空，待补充 |

## 2. 运行后端测试

```bash
cd backend

# 全量
uv run python manage.py test --noinput

# 保留测试库，加快重复执行
uv run python manage.py test --noinput --keepdb

# 指定模块 + 详细输出
uv run python manage.py test search notifications -v 2 --keepdb

# 指定文件
uv run python manage.py test tests.test_points_notifications -v 2 --keepdb
```

说明：

- 测试使用 MySQL 测试库，需要 MySQL 可连接；首次运行会创建 `test_<DB_NAME>`。
- `CELERY_TASK_ALWAYS_EAGER` 在测试类中通过 `@override_settings` 开启，
  任务会同步执行，避免依赖 Worker。
- 测试中涉及 Redis/ES 的行为通过 mock 或降级逻辑隔离，不要求本地 ES 可用。

## 3. 提交前检查

```bash
cd backend
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py test --noinput --keepdb

cd ../frontend
pnpm type-check
pnpm build
```

预期：

- Ruff / ESLint 无错误
- 依赖审计无 high/critical 漏洞
- Django 系统检查无问题
- 无迁移漂移
- 测试全部通过
- TypeScript 无错误、构建成功

## 4. CI 门禁

GitHub Actions 工作流：[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)。

触发条件：

- push 到 `main` / `master`
- 针对 `main` / `master` 的 pull request
- 手动 `workflow_dispatch`

### 4.1 Backend job

| 步骤 | 命令 |
|---|---|
| 安装依赖 | `uv sync --frozen` |
| 代码检查 | `ruff check .` |
| 依赖审计 | `pip-audit --path .venv` |
| 系统检查 | `manage.py check` |
| 迁移漂移 | `makemigrations --check --dry-run` |
| 全量测试 | `manage.py test --noinput` |

> Ruff 当前启用 `E4/E7/E9/F`，优先阻断语法错误、未定义名称和未使用导入；迁移目录不参与检查。

CI 使用 MySQL 8.0 service，并通过 `config/settings_ci.py` 覆盖测试配置：

```env
DJANGO_SETTINGS_MODULE=config.settings_ci
```

`settings_ci.py` 包含：

- `DEBUG=True`，使用内存缓存与内存 Channel Layer
- Celery eager 模式
- 快速密码哈希（MD5），缩短测试时间
- ES 指向不可用地址，验证搜索降级路径

> `config/settings_ci.py` 仅用于 CI，禁止用于生产或日常开发。

### 4.2 Frontend job

| 步骤 | 命令 |
|---|---|
| 安装依赖 | `pnpm install --frozen-lockfile` |
| 代码检查 | `pnpm lint` |
| 依赖审计 | `pnpm audit --audit-level high --prod --registry https://registry.npmjs.org` |
| 类型检查 + 构建 | `pnpm build` |

> 默认镜像源（npmmirror）不提供 npm audit 接口，因此依赖审计显式使用官方 registry。
> ESLint 使用 Vue essential + typescript-eslint recommended，并按项目现状放宽 `any` 等规则。

环境：Node.js 22、pnpm 11、`NODE_OPTIONS=--max-old-space-size=4096`。

### 4.3 本地等价命令

```bash
# 后端
cd backend
uv sync --frozen
uv run ruff check .
uv run pip-audit --path .venv
uv run python manage.py check
DJANGO_SETTINGS_MODULE=config.settings_ci uv run python manage.py makemigrations --check --dry-run
DJANGO_SETTINGS_MODULE=config.settings_ci uv run python manage.py test --noinput

# 前端
cd frontend
pnpm install --frozen-lockfile
pnpm lint
pnpm audit --audit-level high --prod --registry https://registry.npmjs.org
pnpm build
```

### 4.4 分支保护建议

在 GitHub 仓库设置中开启：

- 要求 PR 通过 `Backend checks & tests` 与 `Frontend type-check & build`
- 禁止直接 push 到 `main`
- 合并前要求分支与 `main` 同步

## 5. 集成脚本

`backend/tests/integration/` 下的脚本不是 Django 测试用例，而是需要真实服务的冒烟脚本：

```bash
# 1. 启动后端，并确保存在 admin/admin123（python start_server.py --create-admin）
# 2. 执行
cd backend
uv run python tests/integration/test_full_api.py
uv run python tests/integration/test_ws_simple.py
```

可覆盖的服务地址：

```bash
# test_full_api.py
SMOKE_TEST_BASE_URL=http://localhost:8000/api uv run python tests/integration/test_full_api.py
```

注意：这些脚本会写入数据库（登录、签到、发帖等），不要对生产环境执行。

## 6. 编写测试的建议

1. **接口测试优先**：使用 `APIClient`，覆盖成功、未登录、无权限、参数错误四类。
2. **异步任务显式 eager**：在测试类上使用
   `@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)`。
3. **避免依赖执行顺序**：积分、签到等用例使用独立用户。
4. **ES 相关**：mock `es_is_available` 返回 `False`，验证降级查询；再 mock `True` 验证索引任务。
5. **WebSocket**：可参考 `chat/tests.py` 使用 `WebsocketCommunicator`；
   仅测试消费者逻辑时优先 mock channel layer。
6. **通知**：断言 `Notification` 记录与 `group_send` 调用，不要依赖真实网络。

## 7. 覆盖率缺口

当前优先补充：

- `private_messages`：会话列表、已读、越权访问
- `friendships`：好友请求状态流转、重复请求
- `favorites`：多态收藏、重复收藏
- `activities`：动态可见性、点赞幂等
- `content`：草稿/提交/审核/驳回状态机

## 8. 常见测试问题

| 现象 | 原因 | 处理 |
|---|---|---|
| `Unknown database 'test_university_exchange'` | MySQL 不可用或无权限 | 启动 MySQL，确认账号可建库 |
| Celery 任务未执行 | 未开启 eager | 在测试类上 `override_settings` |
| ES 连接超时 | 测试未 mock | mock `es_is_available` 或设置 `ELASTICSEARCH_FALLBACK_TO_DB=True` |
| 401 | 测试未认证 | `client.force_authenticate(user=...)` 或登录获取 JWT |
| 迁移报错 | 模型与迁移不一致 | 先 `makemigrations`，再跑测试 |
