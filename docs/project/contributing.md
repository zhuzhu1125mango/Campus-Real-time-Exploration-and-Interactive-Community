# 贡献指南

## 1. 开始之前

1. 阅读 [安装](../getting-started/installation.md) 与 [快速开始](../getting-started/quickstart.md) 跑通本地环境。
2. 阅读 [开发指南](../guides/development.md) 了解代码约定。
3. 较大的改动先提 Issue 说明背景、方案与影响范围，避免无效实现。

## 2. 分支与提交

### 2.1 分支

```text
master                # 主分支，保持可运行
feat/<topic>          # 新功能
fix/<topic>           # 缺陷修复
docs/<topic>          # 文档
refactor/<topic>      # 重构
chore/<topic>         # 构建、依赖、脚本
```

### 2.2 提交信息

采用 Conventional Commits 风格：

```text
feat: 新增课程收藏能力
fix: 修复私信 WebSocket 分组错误
docs: 重构文档目录结构
refactor: 拆分 notifications app
test: 补充私聊接口测试
chore: 升级 uv.lock
```

要求：

- 标题简洁，说明「做了什么」
- 正文说明「为什么」以及不明显的取舍
- 一个提交只做一类事情
- 不提交密钥、`.env`、构建产物、日志

## 3. 代码规范

### 3.1 后端

- Python 3.12，遵守 PEP 8
- 使用 `uv` 管理依赖
- 新增 ViewSet 继承 `core/base_viewsets.py`
- 权限/限流通过 `permission_config` / `throttle_config` 声明
- 富文本入库前必须 `sanitize_html`
- 异步副作用通过 Celery，并遵守 `transaction.on_commit`
- 一次性积分必须幂等
- 迁移文件必须提交，且与模型一致

### 3.2 H5

- Vue 3 `<script setup lang="ts">`
- 使用 `pnpm`
- 请求统一走 `utils/request.ts` 与 `api/`
- `v-html` 必须经过 `utils/xss.ts`
- 新增页面同步更新 `router/index.ts`
- 提交前 `pnpm type-check`

### 3.3 小程序

- 页面在 `pages.json` 注册
- 环境变量只使用 `VUE_APP_*`
- 不硬编码 IP/域名
- WebSocket 使用 `getWebSocketUrl` / `getWebSocketProtocols`
- 页面卸载时清理定时器与连接

### 3.4 共享代码

修改 `shared/` 后必须同时验证 H5 与小程序。

## 4. 提交前检查

```bash
# 后端
cd backend
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py test --noinput --keepdb

# 前端
cd frontend
pnpm type-check
pnpm build
```

## 5. PR 检查清单

### 功能

- [ ] 需求/Issue 已关联
- [ ] 主要路径与异常路径都覆盖
- [ ] 权限、限流、分页符合现有约定
- [ ] 不破坏公共聊天室与 H5 私信共存
- [ ] 公开聊天室仍然可用

### 数据与异步

- [ ] 迁移已提交且无漂移
- [ ] 积分/通知/索引副作用已考虑
- [ ] 任务可重试、可幂等
- [ ] 事务提交后才派发任务

### 安全

- [ ] 富文本已清洗
- [ ] 没有硬编码密钥/内网地址
- [ ] 文件上传有类型/大小限制
- [ ] 新增接口有权限控制

### 文档

- [ ] API 路径/参数变化已更新 `docs/reference/api/`
- [ ] 模型变化已更新 `docs/reference/data-model.md`
- [ ] 环境变量变化已更新 `docs/getting-started/configuration.md`
- [ ] 部署/脚本变化已更新 `docs/guides/deployment.md`
- [ ] 新增已知限制已写入 `docs/project/roadmap.md`

### 验证

- [ ] 后端测试通过
- [ ] 前端类型检查/构建通过
- [ ] 至少手工验证一次关键页面
- [ ] WebSocket 相关改动已验证连接、收发、重连

## 6. 评审约定

评审关注：

1. 正确性：边界、并发、权限、事务
2. 一致性：是否复用现有基类/工具/通知入口
3. 可维护性：命名、分层、重复代码
4. 性能：N+1、索引、缓存
5. 安全：XSS、越权、密钥、上传
6. 文档：是否同步更新

评审意见使用「必须修改 / 建议 / 可选」区分优先级。

## 7. 文档贡献

- 文档放在 `docs/` 对应分类下
- 使用中文，代码/路径/命令保持原样
- 接口文档必须能对应到实际路由
- 过时文档移入 `docs/archive/`，不要直接删除
- 文档中的示例域名、密码、证书路径必须是占位符

## 8. 发布流程

1. 确认 `master` 通过检查
2. 更新 [变更记录](changelog.md)
3. 打 tag（建议语义化版本）
4. 按 [部署指南](../guides/deployment.md) 发布
5. 发布后执行健康检查与关键路径回归
