# 论坛 API

前缀：`/api/`（不是 `/api/forum/`）。

## 1. 分类与板块

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/categories/` | 读公开/写管理员 | 论坛分类 |
| GET/PATCH/PUT/DELETE | `/api/categories/{id}/` | 管理员 | 分类管理 |
| GET/POST | `/api/boards/` | 读公开/写管理员 | 板块列表/创建 |
| GET/PATCH/PUT/DELETE | `/api/boards/{id}/` | 读公开/写管理员 | 板块详情/管理 |
| GET/POST | `/api/boards/{id}/topics/` | 读公开/写登录 | 板块主题 |
| GET | `/api/boards/{id}/active_topics/` | 公开 | 活跃主题 |

板块与学校是一对一关系，创建学校时会自动创建对应板块。
列表参数：`page`、`page_size`、`search`。

## 2. 主题

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/api/topics/` | 公开 | 主题列表 |
| POST | `/api/topics/` | 登录 | 创建主题 |
| GET/PATCH/PUT/DELETE | `/api/topics/{id}/` | 读公开/所有者写 | 主题详情/编辑/删除 |
| GET/POST | `/api/topics/{id}/posts/` | 读公开/写登录 | 主题内帖子 |
| POST/DELETE | `/api/topics/{id}/bookmark/` | 登录 | 收藏/取消收藏 |
| POST | `/api/topics/{id}/close/` | 所有者/管理员 | 关闭主题 |

主题列表参数：

| 参数 | 说明 |
|---|---|
| `board` | 板块 ID |
| `status` | `normal`/`pinned`/`announcement`/`closed`/`hidden` |
| `tag` | 标签 ID |
| `author` | 作者 ID |
| `search` | 标题/内容搜索 |
| `ordering` | 排序字段，默认 `-created_at` |
| `page` / `page_size` | 分页 |

主题状态：

| 状态 | 含义 |
|---|---|
| `normal` | 正常 |
| `pinned` | 置顶 |
| `announcement` | 公告 |
| `closed` | 已关闭 |
| `hidden` | 已隐藏 |

## 3. 帖子

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/api/posts/` | 公开 | 帖子列表 |
| POST | `/api/posts/` | 登录 | 发帖 |
| GET/PATCH/PUT/DELETE | `/api/posts/{id}/` | 读公开/所有者写 | 帖子详情/编辑/删除 |
| POST | `/api/posts/{id}/like/` | 登录 | 点赞 |
| DELETE | `/api/posts/{id}/like/` | 登录 | 取消点赞 |
| POST | `/api/posts/{id}/unlike/` | 登录 | 取消点赞（等价） |
| POST | `/api/posts/{id}/report/` | 登录 | 举报 |
| GET | `/api/posts/pending_review/` | 管理员 | 待审核帖子 |

帖子列表参数：`board`、`author`、`topic`、`status`、`search`、`page`、`page_size`。

审核状态：

| 状态 | 含义 |
|---|---|
| `pending` | 待审核 |
| `approved` | 已通过（默认） |
| `rejected` | 已拒绝 |
| `flagged` | 标记审查 |

> 帖子正文是 HTML，入库前由后端 `bleach` 清洗；前端渲染必须经过 XSS 过滤。

## 4. 评论

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/comments/` | 读公开/写登录 | 评论列表/创建 |
| GET/PATCH/PUT/DELETE | `/api/comments/{id}/` | 读公开/所有者写 | 评论详情/编辑/删除 |
| POST | `/api/comments/{id}/like/` | 登录 | 点赞评论 |
| DELETE | `/api/comments/{id}/like/` | 登录 | 取消点赞 |
| POST | `/api/comments/{id}/report/` | 登录 | 举报评论 |
| POST | `/api/comments/{id}/approve/` | 管理员 | 通过 |
| POST | `/api/comments/{id}/disapprove/` | 管理员 | 拒绝 |

评论支持 `parent` 实现多级回复。列表参数：`post`、`author`、`search`。

## 5. 标签

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/tags/` | 读公开/写登录 | 标签列表/创建 |
| GET/PATCH/PUT/DELETE | `/api/tags/{id}/` | 读公开/管理员写 | 标签详情/管理 |
| GET | `/api/tags/hot/` | 公开 | 热门标签，`?limit=` |
| GET | `/api/tags/{id}/topics/` | 公开 | 标签下主题 |

## 6. 书签

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/bookmarks/` | 登录 | 我的书签 |
| GET/PATCH/PUT/DELETE | `/api/bookmarks/{id}/` | 所有者 | 书签详情/删除 |
| DELETE | `/api/bookmarks/unbookmark/` | 登录 | 按 `topic` 取消收藏 |
| GET | `/api/my-bookmarks/` | 登录 | 我的收藏主题（分页） |

## 7. 统计与热门

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/api/stats/` | 公开 | 论坛统计（用户/主题/帖子/板块数） |
| GET | `/api/hot-topics/?days=7` | 公开 | 热门主题（分页） |
| GET | `/api/my-bookmarks/` | 登录 | 我的收藏主题 |

## 8. 通知

论坛不再暴露独立的 `/api/notifications/` 接口。
所有通知统一通过 `/api/users/notifications/` 访问，详见
[聊天与通知](chat-and-notifications.md)。

## 9. 权限与限流

- 浏览：公开
- 发帖/评论/点赞/收藏/举报：登录
- 编辑/删除：作者或管理员
- 审核/关闭/置顶：管理员或板块版主
- 列表/搜索走 `SearchThrottle`，写入走 `WriteThrottle`

## 10. 积分触发

| 行为 | 积分 |
|---|---|
| 发帖 | +10 |
| 回复 | +5 |
| 评论 | +5 |
| 点赞 | +2 |
| 被点赞 | +3 |
| 收藏主题 | +2 |

积分异步发放，接口返回不代表积分已到账。
