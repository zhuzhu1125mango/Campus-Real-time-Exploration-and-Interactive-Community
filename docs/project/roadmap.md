# 路线图与已知缺口

本文记录当前代码中确认存在的问题、测试缺口与后续计划。
优先级：

- **P0**：影响核心功能或安全
- **P1**：影响部分功能或可维护性
- **P2**：优化项

## 1. 缺陷

| 优先级 | 问题 | 位置 | 建议 |
|---|---|---|---|
| P2 | `VITE_API_BASE_URL` 未被读取 | `frontend/src/utils/config.ts` | 统一为环境变量或删除无效配置 |
| P2 | 小程序 API 索引未导出 `searchApi` | `mp-weixin/api/index.js` | 补充导出 |
| P2 | 通知消费者事件名与下发类型不一致 | `backend/chat/consumers.py` | 统一命名，补充协议测试 |

### 已修复（2026-11-13）

- 删除 `forum` 中与新通知模型不兼容的遗留 `NotificationViewSet`，旧 `/api/notifications/` 不再暴露。
- 移除 `forum/urls.py` 中被 Router detail 路由抢占的 `notifications/mark-all-read/` 路径。
- H5 与小程序通知页统一改用 `/api/users/notifications/`。
- 为 `docker-compose.prod.yml` 的 `django-init` 补齐与 `django-http` 一致的环境变量。

## 2. 测试缺口

| 模块 | 现状 | 目标 |
|---|---|---|
| `private_messages` | 空测试文件 | 会话、已读、越权 |
| `friendships` | 空测试文件 | 请求状态流转、重复请求 |
| `favorites` | 空测试文件 | 多态收藏、重复收藏 |
| `activities` | 空测试文件 | 可见性、点赞幂等 |
| `content` | 空测试文件 | 状态机、审核权限 |
| 前端 | 无单元/E2E | 引入 Vitest + Playwright |
| 小程序 | 手动 | 关键页面回归清单 |

## 3. 功能

### 3.1 实时通信

- [ ] 消息撤回
- [ ] 输入中状态
- [ ] 离线消息补推
- [ ] 公共聊天室敏感词过滤
- [ ] WebSocket 连接指标与告警

### 3.2 学习

- [ ] 付费课程支付流程
- [ ] 课程证书
- [ ] 学习提醒

### 3.3 内容

- [ ] 内容点赞接口补齐
- [ ] 富文本图片上传与清理
- [ ] 内容举报流程

### 3.4 小程序

- [ ] 与 H5 功能对齐检查
- [ ] 分享卡片与深链
- [ ] 订阅消息通知

## 4. 运维与质量

- [ ] 接入 Flower 监控 Celery
- [ ] 接入 ELK/Loki 日志聚合
- [ ] 增加 ES/Redis/MySQL 指标与告警
- [x] CI：lint、测试、迁移检查、依赖扫描（Ruff、ESLint、pip-audit、pnpm audit）
- [ ] 增加 OpenAPI/Swagger 文档
- [ ] 统一分页默认值（12 vs 10）
- [ ] 清理根目录/后端临时文件（日志、`data.json`、调试脚本）
- [ ] 生产禁用调试接口

## 5. 安全

- [ ] 生产开启短信验证码
- [ ] 限制调试接口访问
- [ ] 日志脱敏（token、手机号、邮箱）
- [x] 依赖漏洞扫描（CI 使用 pip-audit 与 pnpm audit）
- [ ] 上传文件病毒扫描/对象存储

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
