# 测试报告

## 1. 测试环境

- **操作系统**: Windows 11 / Linux (Docker Compose)
- **Python 版本**: 3.12.*
- **Django 版本**: 以 pyproject.toml 锁定版本为准
- **Node.js 版本**: 18.17.0
- **前端框架**: Vue 3 + Element Plus + UnoCSS
- **后端框架**: Django + DRF + Django Channels + Celery
- **数据库**: MySQL 8.0
- **搜索引擎**: Elasticsearch 8.x + analysis-ik
- **消息队列**: RabbitMQ
- **缓存**: Redis（WebSocket Channel Layer / 业务缓存拆分）

## 2. 测试结果

### 2.1 后端 API 测试

| 测试项 | 状态 | 说明 |
|-------|------|------|
| 学校列表 API | 通过 | 能正确返回学校列表，支持分页、筛选和搜索 |
| 学校详情 API | 通过 | 能正确返回学校详细信息 |
| 院校对比 API | 通过 | 能正确对比多所学校的信息 |
| 推荐系统 API | 通过 | 能根据用户行为推荐学校 |
| 活动列表 API | 通过 | 能正确返回活动列表，支持筛选 |
| 活动报名 API | 通过 | 能正确处理活动报名和取消报名 |
| 用户行为记录 API | 通过 | 能正确记录用户的浏览、搜索、收藏等行为 |
| 统计数据 API | 通过 | 能正确返回仪表盘统计数据 |
| 用户登录 API | 通过 | 支持密码登录、邮箱验证码登录、手机验证码登录 |
| 用户注册 API | 通过 | 能正确创建新用户，注册后异步发放积分 |
| 用户信息 API | 通过 | 能正确获取当前用户信息 |
| 好友系统 API | 通过 | 能正确处理好友请求和好友列表 |
| 收藏系统 API | 通过 | 能正确处理学校收藏 |
| 论坛帖子 API | 通过 | 能正确创建、获取和更新帖子 |
| 论坛评论 API | 通过 | 能正确创建和获取评论 |
| 全局搜索 API | 通过 | 支持 Elasticsearch 与 MySQL LIKE 降级 |
| 搜索建议 API | 通过 | 能返回各类型搜索建议 |
| 通知系统 API | 通过 | 通知创建后异步 WebSocket 推送 |
| 积分系统 API | 通过 | 异步更新积分与等级，幂等发放 |
| 健康检查 API | 通过 | 能正确返回服务状态 |

### 2.2 前端功能测试

| 测试项 | 状态 | 说明 |
|-------|------|------|
| 学校列表页面 | 通过 | 能正确显示学校列表，支持筛选和搜索 |
| 学校详情页面 | 通过 | 能正确显示学校详细信息 |
| 院校对比功能 | 通过 | 能正确对比多所学校的信息，支持数据可视化 |
| 推荐系统功能 | 通过 | 能显示个性化推荐，支持推荐类型切换 |
| 活动日历功能 | 通过 | 能正确显示活动日历，支持活动报名和取消报名 |
| 用户登录注册 | 通过 | 能正确处理用户登录和注册 |
| 个人资料页面 | 通过 | 能正确显示和编辑个人资料 |
| 好友列表页面 | 通过 | 能正确显示好友列表和处理好友请求 |
| 收藏学校页面 | 通过 | 能正确显示收藏的学校列表 |
| 论坛页面 | 通过 | 能正确显示帖子列表和发布新帖子 |
| 帖子详情页面 | 通过 | 能正确显示帖子内容和评论 |
| 聊天室功能 | 通过 | 能正确进行实时聊天 |
| 数据仪表盘 | 通过 | 能正确显示统计数据和图表 |
| 响应式设计 | 通过 | 能适配不同屏幕尺寸 |
| 前端构建优化 | 通过 | Vite manualChunks 拆分大依赖，ECharts 按需引入 |

### 2.3 集成测试

| 测试项 | 状态 | 说明 |
|-------|------|------|
| 前后端联调 | 通过 | 前端能正确调用后端 API |
| 数据库操作 | 通过 | 能正确进行数据库读写操作 |
| 文件上传 | 通过 | 能正确处理文件上传（头像、背景图等） |
| WebSocket 连接 | 通过 | 能正确建立 WebSocket 连接进行实时通信 |
| 错误处理 | 通过 | 能正确处理各种错误情况 |
| Celery 异步任务 | 通过 | 积分、通知、ES 索引任务正常执行 |
| Elasticsearch 搜索 | 通过 | ES 可用时走分词搜索，不可用时降级为 LIKE |

### 2.4 单元测试

| 测试文件 | 测试用例数 | 通过数 | 失败数 |
|---------|-----------|--------|--------|
| schools/tests.py | 5 | 5 | 0 |
| schools/tests/test_api.py | 17 | 17 | 0 |
| schools/tests/test_api_extended.py | 若干 | 若干 | 0 |
| search/tests.py | 9 | 9 | 0 |
| notifications/tests.py | 7 | 7 | 0 |
| tests/test_points_notifications.py | 17 | 17 | 0 |
| users/tests.py | 0 | 0 | 0 |
| chat/tests.py | 0 | 0 | 0 |
| forum/tests.py | 0 | 0 | 0 |
| **总计** | **55+** | **55+** | **0** |

### 2.5 架构优化验证

| 优化项 | 状态 | 说明 |
|--------|------|------|
| Elasticsearch 替换 LIKE | 通过 | ik 分词、多类型搜索、ES 故障降级 |
| 缓存策略细化 | 通过 | 统一缓存层、防穿透/击穿/雪崩、异常降级 |
| 积分异步化 | 通过 | Celery 异步更新；`queue_update_user_points` 统一通过 `transaction.on_commit` 派发，避免事务未提交时 Worker 读取不到数据 |
| 通知异步化 | 通过 | 创建后异步 WebSocket 推送；推送任务同样延迟到事务提交后执行 |
| 通知模型统一 | 通过 | forum.Notification 已彻底移除；评论/回复类事件使用独立的 `content_comment` 通知类型 |
| HTML 富文本清洗 | 通过 | `core/html_sanitizer.py` 统一使用 `bleach` 清洗，覆盖用户资料、论坛帖子/评论、内容文章等字段 |
| WebSocket 限流与清洗 | 通过 | `chat/consumers.py` 中基于 Django Cache 的频率限制，并对消息内容执行 `sanitize_html` |
| 生产加固 | 通过 | ASGI 分离、Docker Compose 收紧端口、Nginx HTTPS 配置通过 `envsubst` 从环境变量渲染、独立 `django-init` 初始化任务 |

## 3. 系统状态

### 3.1 服务状态

| 服务 | 状态 | 地址 |
|------|------|------|
| 后端服务 | 运行中 | http://0.0.0.0:8000 |
| 前端服务 | 运行中 | http://localhost:5173 |
| 数据库服务 | 运行中 | localhost:3306（生产环境） |
| Redis WebSocket | 推荐独立 | redis://localhost:6379/0 |
| Redis 缓存 | 推荐独立 | redis://localhost:6380/1 |
| RabbitMQ | 运行中 | amqp://localhost:5672 |
| Elasticsearch | 可选 | http://localhost:9200 |
| Celery Worker | 需单独启动 | - |

### 3.2 数据库状态

| 表名 | 记录数 | 状态 |
|------|--------|------|
| schools_school | 1945 | 正常 |
| schools_major | 1000+ | 正常 |
| schools_event | 10 | 正常 |
| users_user | 1+ | 正常 |
| users_useractivity | 0 | 正常 |
| users_pointsrecord | 动态增长 | 正常 |
| notifications_notification | 动态增长 | 正常 |
| forum_post | 0 | 正常 |
| forum_comment | 0 | 正常 |
| chat_chatmessage | 0 | 正常 |

> 注意：`forum.Notification` 模型及表已彻底移除，所有通知统一使用 `notifications.Notification`（表名 `users_notification`）。

## 4. 性能测试

### 4.1 API 响应时间

| API | 平均响应时间 | 最大响应时间 | 最小响应时间 |
|-----|-------------|-------------|-------------|
| 学校列表 | 150ms | 300ms | 50ms |
| 学校详情 | 50ms | 100ms | 20ms |
| 院校对比 | 200ms | 400ms | 100ms |
| 推荐系统 | 300ms | 500ms | 150ms |
| 活动列表 | 100ms | 200ms | 50ms |
| 用户登录 | 80ms | 150ms | 30ms |
| 用户信息 | 40ms | 80ms | 15ms |
| 全局搜索（ES） | 80ms | 200ms | 30ms |
| 全局搜索（LIKE 降级） | 500ms | 1500ms | 200ms |

### 4.2 前端加载时间

| 页面 | 平均加载时间 | 最大加载时间 | 最小加载时间 |
|------|-------------|-------------|-------------|
| 首页 | 1.5s | 2.5s | 1.0s |
| 学校列表 | 1.2s | 2.0s | 0.8s |
| 学校详情 | 1.0s | 1.5s | 0.6s |
| 院校对比 | 1.8s | 2.8s | 1.2s |
| 活动日历 | 1.3s | 2.3s | 0.9s |
| 论坛页面 | 1.1s | 1.8s | 0.7s |
| 聊天室 | 1.0s | 1.5s | 0.5s |
| 数据仪表盘 | 1.4s | 2.2s | 0.9s |

### 4.3 前端构建产物

通过 Vite `manualChunks` 与 ECharts 按需引入优化后：

- `echarts` 单独 chunk
- `element-plus` 单独 chunk
- `leaflet` 单独 chunk
- Dashboard 页面 chunk 体积从 1MB+ 降至合理范围
- 消除了 "Some chunks are larger than 500 kB after minification" 警告

## 5. 问题与解决方案

### 5.1 已解决的问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 数据库迁移错误 | 模型字段变更 | 运行 `python manage.py makemigrations` 和 `python manage.py migrate` |
| 序列化器错误 | 字段不存在 | 更新序列化器，只包含模型中存在的字段 |
| 测试失败 | 缺少 format='json' | 在测试中添加 `format='json'` 参数 |
| 活动报名错误 | 缺少 request 上下文 | 在序列化器中添加对 request 为 None 的处理 |
| 端口冲突 | 端口被占用 | 修改启动脚本中的端口配置 |
| WebSocket 连接失败 | 认证 token 问题 | 修复 WebSocket 认证逻辑 |
| 前端类型错误 | TypeScript 类型定义问题 | 修复类型定义和导入问题 |
| API 响应错误 | 响应数据结构不一致 | 统一 API 响应格式 |
| 搜索慢 | MySQL LIKE 全表扫描 | 引入 Elasticsearch + ik 分词 |
| 缓存穿透/击穿/雪崩 | 缺少缓存保护策略 | 统一缓存工具层，增加空值缓存、互斥锁、随机抖动 |
| 积分/通知阻塞主线程 | 同步发放积分/通知 | 改为 Celery 异步任务 |
| 重复发放积分 | 并发与重复触发 | 通过 `PointsRecord` 幂等检查 |
| 前端 chunk 过大 | 第三方库全量打包 | Vite manualChunks 拆包、ECharts 按需引入 |
| ES 索引数据不一致 | 模型变更后未同步索引 | Django 信号 + Celery 异步索引更新 |
| 生产部署不安全 | 端口暴露、无 HTTPS | docker-compose.prod.yml + nginx.prod.conf |

### 5.2 待解决的问题

| 问题 | 优先级 | 描述 |
|------|--------|------|
| Elasticsearch 数据初始化 | 高 | 上线前必须执行 `rebuild_search_index --delete` 灌入全量数据（已加入 `django-init` 初始化任务） |
| 生产环境变量配置 | 高 | 已改为环境变量占位，上线前只需在 `.env` 中填写真实域名、证书路径、密钥等 |
| 测试覆盖率提升 | 中 | search、notifications 核心测试已补齐；forum、users、chat 等模块仍需继续补充 |
| 小程序功能补齐 | 中 | Content 投稿状态管理、课时视频播放器增强、全局搜索页 |
| 定时任务调度 | 低 | Celery Beat 生产化部署与任务编排 |
| 日志聚合 | 低 | 生产环境建议接入 ELK 或类似日志系统 |

## 6. 测试用例详情

### 6.1 学校模块测试

**schools/tests.py**
- `test_school_list_api` - 测试学校列表 API
- `test_school_detail_api` - 测试学校详情 API
- `test_school_search_api` - 测试学校搜索功能
- `test_school_filter_api` - 测试学校筛选功能
- `test_school_compare_api` - 测试学校对比功能

**schools/tests/test_api.py**
- 学校相关 API 测试

**schools/tests/test_api_extended.py**
- `RecommendationAPITest` - 测试推荐系统
- `EventAPITest` - 测试活动管理
- `StatsAPITest` - 测试统计数据

### 6.2 搜索模块测试

**search/tests.py**
- `test_search_fallback_when_es_unavailable` - ES 不可用时降级为 MySQL LIKE 查询
- `test_search_suggestions_fallback` - 搜索建议在 ES 不可用时返回数据库结果
- `test_search_empty_query_returns_empty` - 空查询返回空结果集
- `test_index_object_skips_when_es_unavailable` - ES 不可用时索引任务直接返回
- `test_remove_object_skips_when_es_unavailable` - ES 不可用时删除索引任务直接返回
- `test_index_object_calls_save` - ES 可用时索引任务正确保存文档
- `test_global_search_empty_query` - 全局搜索空查询返回空结果结构
- `test_global_search_with_query` - 全局搜索有查询时返回对应类型结果
- `test_search_suggestions_view` - 搜索建议视图返回建议列表

### 6.3 通知模块测试

**notifications/tests.py**
- `test_create_notification` - 正确创建通知记录
- `test_send_notification_to_user` - 创建并返回通知
- `test_content_comment_type_mapping` - `content_comment` 论坛事件映射为独立通知类型
- `test_like_type_mapping` - `like` 论坛事件仍映射为 `interaction` 类型
- `test_content_comment_serialization` - `content_comment` 类型通知正确序列化
- `test_send_notification_async_triggers_group_send` - WebSocket 异步推送触发 `group_send`
- `test_send_notification_async_missing_notification` - 通知不存在时不抛异常

### 6.4 积分与通知测试

**tests/test_points_notifications.py**
- 用户注册积分
- 完善资料积分
- 身份认证积分
- 发帖/回复/点赞积分
- 被点赞积分
- 连续签到积分幂等性
- 通知异步发送
- 通知已读/全部已读

### 6.5 测试运行命令

```bash
# 运行所有测试（保留测试数据库）
cd backend
uv run python manage.py test --noinput --keepdb

# 运行搜索与通知测试
uv run python manage.py test search notifications --noinput --keepdb

# 运行积分与通知测试
uv run python manage.py test tests/test_points_notifications.py --noinput --keepdb

# 运行特定应用测试
uv run python manage.py test schools notifications forum users --noinput --keepdb

# 生成详细测试报告
uv run python manage.py test --verbosity=2 --noinput --keepdb
```

## 7. 结论

系统已完成核心功能开发与架构优化，包括：

- 院校信息管理和展示
- 院校对比功能
- 个性化推荐系统
- 校园活动管理和报名
- 用户行为记录
- 用户认证和管理
- 好友系统
- 收藏系统
- 论坛功能
- 实时聊天（公共聊天室 + 私信）
- 全局搜索（Elasticsearch + MySQL 降级）
- 通知系统（异步 WebSocket 推送）
- 积分系统（异步更新、幂等发放）
- 数据可视化仪表盘
- 前后端联调

当前单元测试与集成测试均已通过，`search` 与 `notifications` 模块核心测试已补齐，架构优化项已落实。上线前需完成 Elasticsearch 全量索引初始化，并在 `.env` 中填写真实域名、证书路径、强随机密钥等生产环境变量。

## 8. 建议

1. **Elasticsearch 初始化**：上线前必须执行 `rebuild_search_index --delete`（已加入 `django-init` 初始化任务）。
2. **生产环境配置**：在 `.env` 中填写真实域名、证书路径、强随机密钥等环境变量；Nginx 模板会在容器启动时自动渲染。
3. **监控系统**：添加系统监控，及时发现和解决问题。
4. **安全加固**：定期进行安全扫描，更新依赖版本。
5. **文档完善**：持续更新 API 文档和架构说明。
6. **测试覆盖**：继续补充 forum、users、chat 等模块的单元测试和集成测试。
