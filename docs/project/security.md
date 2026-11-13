# 安全说明

## 1. 安全基线

| 层面 | 措施 | 代码/配置 |
|---|---|---|
| 密钥 | 生产必须显式设置 `DJANGO_SECRET_KEY` | `config/settings.py` |
| 调试 | 生产 `DJANGO_DEBUG=False` | 环境变量 |
| 主机 | `ALLOWED_HOSTS` 白名单 | 环境变量 |
| CORS | 仅允许可信 origin | `CORS_ALLOWED_ORIGINS` |
| CSRF | Cookie + 前端 `X-CSRFToken` | `settings.py`、`utils/request.ts` |
| Cookie | 生产 `Secure`、`HttpOnly`、`SameSite=Lax` | `settings.py` |
| 响应头 | `X-Content-Type-Options`、`X-Frame-Options`、`Referrer-Policy` | Django + Nginx |
| 富文本 | `bleach` 白名单清洗 | `core/html_sanitizer.py` |
| 前端 XSS | DOMPurify 过滤 `v-html` | `frontend/src/utils/xss.ts` |
| WebSocket | JWT 认证、限流、长度限制、HTML 清洗 | `chat/middleware.py`、`chat/consumers.py` |
| 上传 | 头像/横幅类型与大小校验 | `users/validators.py` |
| 依赖 | 锁文件固定版本 | `uv.lock`、`pnpm-lock.yaml` |

## 2. 认证与授权

- JWT access 30 分钟、refresh 1 天，刷新轮换并拉黑旧 refresh。
- 权限优先在 ViewSet 的 `permission_config` 中声明。
- 资源级权限使用 `IsOwnerOrAdmin`。
- 管理员接口使用 `IsAdminUser`。
- 私信 WebSocket 要求好友关系，防止陌生人骚扰。
- 公开接口只返回公开字段（如 `UserPublicSerializer`）。

### 检查要点

- [ ] 新增接口是否默认需要登录？
- [ ] 是否能通过修改 URL 中的 id 越权访问他人资源？
- [ ] 列表接口是否泄露了邮箱、手机号等敏感字段？
- [ ] 管理员 action 是否已限制权限？

## 3. XSS

三层防护：

1. **后端入库清洗**：`sanitize_html` 白名单标签/属性/协议。
2. **前端渲染清洗**：H5 `v-html` 必须使用 `utils/xss.ts`。
3. **小程序**：使用 `shared/utils/xss.js` 或 `rich-text` 白名单。

覆盖字段：

- 用户 `bio`
- 论坛帖子/评论
- 内容正文/摘要/评论/修订
- WebSocket 聊天消息

新增富文本字段时必须在模型 `save()` 中清洗，并在前端渲染处过滤。

## 4. CSRF / CORS

- CSRF：Django 中间件启用；前端从 cookie 读取 `csrftoken` 并写入 `X-CSRFToken`。
- CORS：生产关闭 `CORS_ALLOW_ALL_ORIGINS`，只允许配置的域名。
- 预检请求必须允许 `Authorization`、`Content-Type`、`X-CSRFToken`。

常见错误：

- 生产把 `CORS_ALLOWED_ORIGINS` 配成 `*`
- 前端域名带路径或缺少端口
- Nginx 丢弃了 `Origin` 头

## 5. WebSocket 安全

- token 优先通过 `Sec-WebSocket-Protocol: jwt,<token>` 传递，避免 URL 日志。
- 兼容 `?token=`，但不推荐。
- 频率限制：60 秒 60 条。
- 内容长度 ≤ 1000 字符。
- 消息入库前 `sanitize_html`。
- 私聊要求好友关系。
- 生产必须使用 Redis Channel Layer，避免多进程状态不一致。

## 6. 文件上传

| 类型 | 位置 | 限制 |
|---|---|---|
| 头像 | `users/validators.py` | 图片扩展名 + 大小 |
| 横幅 | `users/validators.py` | 图片扩展名 + 大小 |
| 论坛附件 | `forum.Attachment` | 文件名/大小/类型入库 |
| 学习资源 | `learning.LearningResource` | 文件类型/大小 |
| 内容特色图 | `content.Content.featured_image` | ImageField |

建议：

- 上传目录不执行脚本
- Nginx 对 `/media/` 只提供静态读取
- 生产考虑接入对象存储与病毒扫描

## 7. 限流

| 范围 | 速率 |
|---|---|
| 匿名 | 60/min |
| 用户 | 120/min |
| 登录 | 10/min |
| 验证码 | 3/min |
| 搜索 | 30/min |
| 写操作 | 60/min |

WebSocket 独立限流：60 秒 60 条。

## 8. 部署安全

- 仅暴露 Nginx 80/443；数据库、Redis、RabbitMQ、ES 不对外暴露。
- 强制 HTTPS，80 跳转 443。
- 证书路径通过环境变量注入，不写死域名。
- 数据库/消息队列使用强密码。
- 容器内 `.env` 不打包进镜像（`.dockerignore`）。
- 日志不记录 token、密码、完整请求体。

## 9. 密钥管理

- `.env` 不提交版本库。
- 生产使用环境变量或密钥管理服务。
- 泄露后立即轮换：`DJANGO_SECRET_KEY`、数据库密码、RabbitMQ 密码、短信 AK/SK。
- 轮换 `DJANGO_SECRET_KEY` 会使现有 JWT 失效，需要通知用户重新登录。

## 10. 依赖与漏洞

```bash
# Python
cd backend
uv lock --check
# 可接入 pip-audit / safety

# 前端
cd frontend
pnpm audit
```

建议在 CI 中增加依赖漏洞扫描，并定期升级。

## 11. 已知安全/合规缺口

| 项 | 说明 | 建议 |
|---|---|---|
| 短信默认关闭 | `SMS_ENABLED=False`，开发验证码可能被滥用 | 生产开启并接入真实验证码 |
| 调试接口 | `/api/users/debug-avatar/` 等 | 生产限制访问或移除 |
| 日志级别 | `chat`/`users` 默认 DEBUG | 生产调为 INFO |
| 小程序域名 | 需要 HTTPS/WSS 与备案 | 上线前完成配置 |
| 无自动化安全扫描 | 当前无 CI 安全任务 | 接入依赖扫描与 SAST |

## 12. 漏洞上报

发现安全问题请勿公开提交 Issue。请通过项目维护者提供的私有渠道联系，
并提供：

- 影响范围与复现步骤
- 受影响的版本/commit
- 可能的修复建议

维护者确认后会尽快修复并在 [变更记录](changelog.md) 中说明。
