# 路线图与已知缺口

本文记录当前代码中确认存在的问题、测试缺口与后续计划。
优先级：

- **P0**：影响核心功能或安全
- **P1**：影响部分功能或可维护性
- **P2**：优化项

## 1. 缺陷

当前无已知 P0/P1/P2 缺陷。

### 已修复（2026-11-14）

- `VITE_API_BASE_URL` 未被读取：`utils/config.ts` 改为读取该变量，缺省 `/api`；`Profile.vue` 媒体地址统一使用 `VITE_MEDIA_BASE_URL`。
- 小程序 API 索引未导出 `searchApi`：`mp-weixin/api/index.js` 已补充命名导出与默认导出的 `search` 字段。
- 通知 WebSocket 事件名不一致：组事件、消费者方法与下发类型统一为 `unread_notifications`。
- 调试接口暴露：`debug-avatar`、`test-static`、`list-avatars`、`test-html-media` 仅在 `DEBUG=True` 时注册路由。
- 内容模块：修复作者无法查看自己的草稿/提交审核、管理员无法审核他人草稿的问题；评论接口 `parent` 改为可选。
- 私信模块：`perform_create` 改为 `serializer.save()`，创建响应包含完整消息数据。

### 已修复（2026-11-13）

- 删除 `forum` 中与新通知模型不兼容的遗留 `NotificationViewSet`，旧 `/api/notifications/` 不再暴露。
- 移除 `forum/urls.py` 中被 Router detail 路由抢占的 `notifications/mark-all-read/` 路径。
- H5 与小程序通知页统一改用 `/api/users/notifications/`。
- 为 `docker-compose.prod.yml` 的 `django-init` 补齐与 `django-http` 一致的环境变量。

## 2. 测试缺口

| 模块 | 现状 | 目标 |
|---|---|---|
| `private_messages` | 已覆盖创建、会话、已读、未读与越权 | 已完成 |
| `friendships` | 已覆盖请求流转、重复请求、好友列表与解除 | 已完成 |
| `favorites` | 已覆盖多态收藏、重复收藏、学校同步与取消 | 已完成 |
| `activities` | 已覆盖可见性、点赞幂等、评论与关注流 | 已完成 |
| `content` | 已覆盖可见性、修订、审核状态机与评论 | 已完成 |
| 前端 | Vitest 单测 + Playwright E2E（首页/鉴权/论坛核心流程） | 已覆盖核心流程 |
| 小程序 | 手动 | 关键页面回归清单 |

## 3. 功能

### 3.1 实时通信

- [x] 消息撤回（REST + WebSocket `message_recalled`）
- [x] 输入中状态（公共聊天室与私信）
- [ ] 离线消息补推
- [x] 公共聊天室敏感词过滤（`core/sensitive_filter.py`）
- [ ] WebSocket 连接指标与告警

### 3.2 学习

- [x] 付费课程支付流程（`PaymentOrder` + 模拟支付，`/api/learning/orders/`）
- [x] 课程证书（完成课程自动发证，`/api/learning/certificates/`，支持编号校验）
- [x] 学习提醒（`StudyReminder` + Celery Beat 每 10 分钟扫描，站内通知/订阅消息）

### 3.3 内容

- [x] 内容点赞接口补齐（`ContentLike` + `like`/`unlike` + `is_liked`）
- [x] 富文本图片上传与清理（`/api/content/images/` + `cleanup_content_images`）
- [x] 内容举报流程（`ContentReport` + 举报接口 + 管理员处理）

### 3.4 小程序

- [x] 与 H5 功能对齐检查（差异清单见 [小程序指南](../guides/mini-program.md)，剩余页面已补齐）
- [x] 分享卡片与深链
- [x] 订阅消息通知

## 4. 运维与质量

- [x] 接入 Flower 监控 Celery
- [x] 接入 Loki 日志聚合（Promtail 采集容器日志，Grafana 查询，`--profile monitoring`）
- [x] 增加 ES/Redis/MySQL 指标与告警（Prometheus + Grafana，`--profile monitoring`）
- [x] CI：lint、测试、迁移检查、依赖扫描（Ruff、ESLint、pip-audit、pnpm audit）
- [x] 增加 OpenAPI/Swagger 文档（`/api/schema/`、`/api/swagger/`、`/api/redoc/`）
- [x] 统一分页默认值（全局与 `BaseModelViewSet` 均为 12）
- [x] 清理根目录/后端临时文件（日志、`data.json`、调试脚本）

## 5. 安全

- [x] 生产开启短信验证码（`SMS_ENABLED` 改由环境变量控制，部署时设为 `True`）
- [x] 日志脱敏（token、手机号、邮箱）
- [x] 依赖漏洞扫描（CI 使用 pip-audit 与 pnpm audit）
- [x] 上传文件病毒扫描（ClamAV，`--profile security`）
- [ ] 对象存储（OSS/COS）

## 6. 文档

- [x] 文档目录重构
- [x] API 分模块文档
- [x] 数据模型与 WebSocket 协议
- [x] 部署、运维、排障
- [ ] 为关键流程补充时序图
- [ ] 为管理后台补充操作手册
- [ ] 增加英文版 README（可选）

## 7. 维护规则

- 修复缺陷后从本文移除对应条目，并在 [变更记录](changelog.md) 中记录。
- 新增已知限制时同步写入本文，避免只存在于聊天记录或 Issue 中。
- 每季度复核一次优先级。
