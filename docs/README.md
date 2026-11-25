# 项目文档中心

本目录是 Campus Real-time Exploration and Interactive Community 的唯一文档入口。
文档组织参考 [Diátaxis](https://diataxis.fr/) 的四种文档类型（入门、指南、参考、解释），
并结合常见开源项目的目录习惯，按「读者目标」而不是按代码目录划分。

> 文档基线：2026-11-13。所有接口路径、模型字段、环境变量均以当前仓库代码为准。
> 代码变更导致行为变化时，应在同一个 PR 中同步更新对应文档。

## 我应该读哪一篇

| 你的目标 | 建议阅读 |
|---|---|
| 第一次把项目跑起来 | [安装](getting-started/installation.md) → [快速开始](getting-started/quickstart.md) |
| 配置环境变量、数据库、Redis、ES | [配置说明](getting-started/configuration.md) |
| 参与开发、了解代码约定 | [开发指南](guides/development.md) |
| 运行测试、补充测试 | [测试指南](guides/testing.md) |
| 部署到测试/生产环境 | [部署指南](guides/deployment.md) |
| 日常运维、排障 | [运维手册](guides/operations.md)、[故障排查](guides/troubleshooting.md) |
| 小程序开发与对齐 | [小程序指南](guides/mini-program.md) |
| 理解系统设计 | [架构总览](architecture/overview.md) |
| 查接口、字段、WebSocket 协议 | [参考文档](reference/api/README.md) |
| 提交代码、了解安全要求 | [贡献指南](project/contributing.md)、[安全说明](project/security.md) |
| 了解本次重构的范围与影响 | [重构变更摘要](project/refactor-summary-2026-11-13.md) |

## 目录结构

```text
docs/
├── README.md                       # 文档中心（本文件）
├── getting-started/                # 入门：安装、快速开始、配置
│   ├── installation.md
│   ├── quickstart.md
│   └── configuration.md
├── guides/                         # 指南：面向具体任务的步骤
│   ├── development.md              # 开发约定与扩展方式
│   ├── testing.md                  # 测试策略与命令
│   ├── deployment.md               # 开发/生产部署
│   ├── operations.md               # 运维手册
│   └── troubleshooting.md          # 常见故障排查
├── architecture/                   # 解释：系统为什么这样设计
│   ├── overview.md                 # 系统上下文与关键流程
│   ├── backend.md                  # 后端分层、认证、权限
│   ├── frontend.md                 # H5 架构
│   ├── realtime.md                 # WebSocket / Channels
│   └── async-search-cache.md       # Celery、Elasticsearch、缓存
├── reference/                      # 参考：准确、可查的事实
│   ├── api/                        # REST API 分模块文档
│   │   ├── README.md               # 通用约定 + 接口索引
│   │   ├── users.md
│   │   ├── social.md
│   │   ├── forum.md
│   │   ├── schools.md
│   │   ├── learning.md
│   │   ├── content.md
│   │   ├── chat-and-notifications.md
│   │   └── feed-and-search.md
│   ├── data-model.md               # 数据模型与表清单
│   ├── background-jobs.md          # Celery 任务、积分规则、索引
│   └── websocket-protocol.md       # WebSocket 消息协议
├── project/                        # 项目治理
│   ├── contributing.md             # 贡献流程与规范
│   ├── security.md                 # 安全基线与漏洞上报
│   ├── changelog.md                # 变更记录
│   ├── refactor-summary-2026-11-13.md  # 本次重构摘要
│   └── roadmap.md                  # 已知缺口与规划
└── archive/                        # 历史文档（已过时，仅供追溯）
```

## 项目速览

| 维度 | 说明 |
|---|---|
| 业务 | 院校查询、校园论坛、在线学习、内容中心、好友/私信、实时聊天、通知、积分、全局搜索 |
| 后端 | Python 3.12、Django 6.0、DRF、Channels、Celery |
| H5 | Vue 3、TypeScript、Pinia、Element Plus、UnoCSS、Vite |
| 小程序 | Uni-app（`mp-weixin/`） |
| 数据 | MySQL 8（可选主从）、Redis（WS/缓存拆分）、RabbitMQ、Elasticsearch 8 + ik |
| 部署 | Docker Compose、Nginx、gunicorn + uvicorn worker、独立 WebSocket 进程 |

## 文档写作约定

1. **事实优先**：接口路径以 `backend/config/urls.py` 与各 app 的 `urls.py` / DRF Router 为准；
   环境变量以 `backend/config/settings.py`、`backend/.env.example`、根目录 `.env.example` 为准。
2. **可执行**：命令默认在仓库根目录执行，涉及子目录时会显式标注 `cd`。
3. **区分环境**：涉及 `DEBUG`、Redis、Channel Layer、ES 时，必须写清开发环境与生产环境的差异。
4. **不记录密钥**：示例中的域名、证书路径、密码均为占位符，禁止提交真实凭据。
5. **旧文档处理**：内容被替代后移入 `archive/`，并在文件名中保留归档时间，不直接静默删除。
