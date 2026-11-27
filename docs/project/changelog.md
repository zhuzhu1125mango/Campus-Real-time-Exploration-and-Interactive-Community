# 变更记录

本项目尚未建立正式版本号与 tag。以下记录按日期整理已提交的变更，
以及当前工作区中尚未提交的重构内容。

格式参考 Keep a Changelog，提交类型参考 Conventional Commits。

## Unreleased（当前工作区，未提交）

### 架构与后端

- 按领域拆分 app：新增 `activities`、`favorites`、`friendships`、`private_messages`、
  `notifications`，移除 `users` 下平铺的 friendship/messages/notifications/favorites 模块。
- 新增 `core/`：统一 ViewSet 基类、缓存工具、HTML 清洗。
- 新增 `search` 的 Elasticsearch 实现：文档、客户端、服务、信号、Celery 任务、
  全量重建命令。
- 新增统一通知模型与发送入口，移除 `forum.Notification` 并迁移历史数据。
- 新增积分统一规则 `users/points.py` 与异步任务 `users/tasks.py`。
- 新增数据库读写分离路由 `config/db_router.py`。
- 新增生产部署文件：`backend/Dockerfile`、`nginx/`、`docker-compose.prod.yml`、
  `elasticsearch/`、生产启动脚本。
- 新增 `feed` 聚合流与热门标签。

### 前端与小程序

- H5 新增统一请求层、安全工具、共享工具与 ECharts 按需引入。
- H5 完善聊天、搜索、内容、学习、院校等页面。
- 小程序补齐消息页、搜索页、内容投稿状态、课时播放器、WebSocket 安全连接。
- 新增 `shared/` 三端共享工具。

### 文档

- 重构 `docs/` 目录，按入门、指南、架构、参考、项目治理分类。
- 旧文档移入 `docs/archive/`。
- 新增 API 分模块文档、数据模型、WebSocket 协议、后台任务、运维与排障文档。

### CI

- 新增 `.github/workflows/ci.yml`：
  - 后端：MySQL service、依赖安装、Ruff 检查、pip-audit、系统检查、迁移漂移检查、全量测试
  - 前端：pnpm 冻结安装、ESLint 检查、pnpm audit、TypeScript 类型检查与生产构建
- 后端新增 Ruff 配置与 `pip-audit` 开发依赖。
- 前端新增 ESLint 扁平配置、`typescript-eslint` 与 `pnpm lint` 脚本。
- 升级 `axios`、`dompurify`、`vue` 及传递依赖，修复高危/严重漏洞；pnpm audit 在 high 级别通过。

### Fixed

- 删除与新通知模型不兼容的 `forum.NotificationViewSet`，旧 `/api/notifications/` 返回 404。
- H5 `ForumNotifications`、`Forum` 与小程序通知页改用 `/api/users/notifications/`。
- 移除被 Router detail 路由抢占的 `notifications/mark-all-read/` 路径。
- 内容模块：作者可见自己的草稿、可提交审核；管理员可审核与上下架他人内容；
  评论创建时 `parent` 改为可选。
- 私信模块：创建私信改用 `serializer.save()`，修复响应缺少消息数据的问题。
- 通知 WebSocket 事件统一为 `unread_notifications`，消费者方法与下发类型保持一致。
- 小程序 API 索引补充导出 `searchApi`。
- H5 `VITE_API_BASE_URL` 生效（缺省 `/api`），媒体地址统一由 `VITE_MEDIA_BASE_URL` 控制。
- 调试路由仅在 `DEBUG=True` 时注册，生产环境不再暴露。

### Tests

- 补齐 `private_messages`、`friendships`、`favorites`、`activities`、`content` 五个模块的接口测试。

### Added（2026-11-16）

- 内容点赞：新增 `ContentLike` 模型、`like`/`unlike` 接口与列表 `is_liked` 字段。
- OpenAPI：接入 `drf-spectacular`，新增 `/api/schema/`、`/api/swagger/`、`/api/redoc/`。
- 日志脱敏过滤器 `core/SensitiveDataFilter`，屏蔽 token、手机号与邮箱。
- `SMS_ENABLED` 改为环境变量，生产可开启真实短信。

### Changed（2026-11-16）

- `StandardResultsSetPagination` 默认页大小由 10 调整为 12，与全局 `PAGE_SIZE` 一致。
- 清理后端本地临时文件（`data.json`、运行日志、测试输出）。
- 为 `docker-compose.prod.yml` 的 `django-init` 补齐运行环境变量。
- 修复用户搜索在 ES 降级模式下对已切片 QuerySet 再次过滤导致的 500。
- 修复签到在本地跨日时区下重复/并发校验失效的问题，签到积分改为事务内同步发放。

### Added（2026-11-17）

- 内容举报：新增 `ContentReport` 模型、`report` 接口与管理员处理接口。
- 富文本图片：新增 `ContentImage`、上传接口与 `cleanup_content_images` 清理命令；编辑器改为上传后端而非 base64。
- 实时通信：私信撤回、公共/私信输入中状态、公共聊天室敏感词过滤。
- 前端：接入 Vitest，新增工具函数单测，CI 增加 `pnpm test` 步骤。

### Changed（2026-11-17）

- `Message` 增加 `is_recalled`、`recalled_at` 字段，接口与 WebSocket 同步返回。

### Added（2026-11-25）

- 小程序：注册动态页，内容详情支持点赞/取消/举报，私信与聊天室支持撤回和输入中状态。
- 小程序：首页、内容/帖子/院校/课程/用户详情支持分享卡片与深链。
- 微信订阅消息：新增 openid 绑定、订阅授权接口与 Celery 发送任务，未配置时自动跳过。
- 微信登录：新增 `wechat_login`，已绑定账号可用 code 换取 JWT。
- 文档：新增 [小程序开发与对齐指南](../guides/mini-program.md)。

### Changed（2026-11-25）

- `User` 增加 `wechat_openid`、`wechat_subscriptions` 字段。

### Added（2026-11-26）

- 新增 Flower 服务与 `flower` 生产依赖，Compose 中默认启动并仅绑定本机端口。
- 新增可选监控栈 `--profile monitoring`：Prometheus、Grafana、MySQL/Redis/Elasticsearch Exporter 与告警规则。
- `/api/health/?deep=1` 支持检查数据库、缓存与 Elasticsearch，异常时返回 503。
- 小程序：新增校园活动（列表筛选、详情、报名/取消）、好友管理（列表/请求/添加）、板块详情、标签详情与学习仪表盘页面。
- 前端：接入 Playwright E2E（`frontend/e2e/`），拦截 `/api` 使用固定数据，覆盖首页导航、鉴权守卫、登录成功/失败与论坛进入主题详情；CI 增加 E2E 步骤。
- 学习：新增付费课程下单与模拟支付（`PaymentOrder`、`/api/learning/orders/`），支付成功后自动完成报名。
- 学习：新增课程证书（完成全部课时或手动完成后自动发放），支持我的证书、证书详情、按编号公开校验与管理员撤销；H5 与小程序同步接入。
- 学习：新增学习提醒（`StudyReminder`、`/api/learning/reminders/`），Celery Beat 每 10 分钟扫描并发送站内通知，支持微信订阅消息模板；H5 与小程序可设置每日提醒时间。
- 运维：新增 Loki + Promtail 日志聚合（`--profile monitoring`），Grafana 预置 Loki 数据源，日志默认保留 30 天。
- 安全：新增上传文件病毒扫描（ClamAV，`--profile security`），覆盖头像、富文本图片、论坛附件、课程封面与资源文件，默认关闭、启用后 fail-closed。
- 存储：支持对象存储（S3 兼容：阿里云 OSS / 腾讯云 COS / MinIO），通过 `STORAGE_BACKEND=s3` 切换，默认仍为本地 media。

### 已知问题

- 部分 app 测试为空。
- `VITE_API_BASE_URL` 未被前端实际读取。
- 小程序 API 索引未导出 `searchApi`。
- 详见 [路线图](roadmap.md)。

## 2026-07-06

### Added

- 关注功能贯通 H5、小程序与后端。
- 小程序配置与安全工具、页面体验完善。
- 后端 chat、forum、users、schools 模块测试补齐。
- 后端核心 API 限流。

### Fixed

- 小程序定时器与生命周期泄漏。
- 前端健康检查改用统一请求封装。
- 后端并发、权限、缓存问题。
- 小程序消息页完整实现。

## 2026-07-05

### Added

- 后端 WebSocket 安全认证与在线统计。
- 后端统一权限控制与 DRF 默认认证策略。
- 前端统一请求层与聊天体验优化。
- 小程序请求层与 WebSocket 连接优化。
- 数据库索引优化与 N+1 查询治理。

### Fixed

- 小程序 P0 级基础配置与 API 调用。
- `v-html` 富文本 XSS 过滤。
- 后端权限与敏感信息加固。
- 并发安全与权限问题。

## 更早

更早的提交可通过以下命令查看：

```bash
git log --date=short --pretty=format:"%ad %h %s"
```

## 版本发布约定

正式发版时建议：

1. 使用语义化版本（`vMAJOR.MINOR.PATCH`）
2. 将 `Unreleased` 内容移入对应版本
3. 记录破坏性变更（`BREAKING CHANGE`）
4. 关联数据库迁移与部署注意事项
