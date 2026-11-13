# 内容中心 API

前缀：`/api/content/`。

## 1. 内容类型、分类、标签

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/content/content-types/` | 读公开/写管理员 | 内容类型 |
| GET/PATCH/PUT/DELETE | `/api/content/content-types/{id}/` | 读公开/管理员写 | 类型管理 |
| GET/POST | `/api/content/categories/` | 读公开/写管理员 | 分类 |
| GET/PATCH/PUT/DELETE | `/api/content/categories/{id}/` | 读公开/管理员写 | 分类管理 |
| GET/POST | `/api/content/tags/` | 读公开/写登录 | 标签 |
| GET/PATCH/PUT/DELETE | `/api/content/tags/{id}/` | 读公开/管理员写 | 标签管理 |

## 2. 内容

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/api/content/contents/` | 公开 | 已发布内容列表 |
| POST | `/api/content/contents/` | 登录 | 创建内容 |
| GET | `/api/content/contents/{id}/` | 公开/作者 | 内容详情 |
| PATCH/PUT/DELETE | `/api/content/contents/{id}/` | 作者/管理员 | 更新/删除 |
| GET | `/api/content/contents/my_contents/` | 登录 | 我的内容，可按状态筛选 |
| POST | `/api/content/contents/{id}/submit/` | 作者 | 提交审核 |
| POST | `/api/content/contents/{id}/approve/` | 管理员 | 审核通过 |
| POST | `/api/content/contents/{id}/reject/` | 管理员 | 审核拒绝 |
| POST | `/api/content/contents/{id}/publish/` | 管理员 | 直接发布 |
| POST | `/api/content/contents/{id}/unpublish/` | 管理员 | 撤回发布 |
| GET | `/api/content/contents/{id}/revisions/` | 作者/管理员 | 修订历史 |

### 2.1 状态机

```text
draft ──submit──→ pending ──approve──→ published
  ↑                  │                    │
  │                  └──reject──→ rejected│
  └──────────unpublish───────────────────┘
```

| 状态 | 含义 | 可见性 |
|---|---|---|
| `draft` | 草稿 | 仅作者/管理员 |
| `pending` | 待审核 | 作者/管理员 |
| `published` | 已发布 | 所有人 |
| `rejected` | 已拒绝 | 作者/管理员 |

`is_published` 与 `status` 自动同步：

- `published` → `is_published=True`
- `draft` / `rejected` → `is_published=False`
- 首次发布自动写 `publish_date`

### 2.2 列表与筛选

公开列表只返回 `status=published` 的内容。

`my_contents` 参数：

| 参数 | 说明 |
|---|---|
| `status` | `draft` / `pending` / `published` / `rejected` |
| `search` | 标题/摘要搜索 |
| `page` / `page_size` | 分页 |

### 2.3 创建

```json
{
  "title": "我的校园生活",
  "slug": "my-campus-life",
  "content_type": 1,
  "category": 2,
  "tags": [1, 2],
  "content": "<p>正文</p>",
  "summary": "摘要",
  "status": "draft"
}
```

规则：

- `slug` 唯一
- `content`、`summary` 入库前 `bleach` 清洗
- 默认状态 `draft`
- 作者可创建/编辑自己的内容，管理员可审核

## 3. 内容评论

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/content/comments/` | 读公开/写登录 | 评论列表/创建 |
| GET/PATCH/PUT/DELETE | `/api/content/comments/{id}/` | 读公开/本人写 | 评论管理 |
| POST | `/api/content/comments/{id}/approve/` | 管理员 | 通过 |
| POST | `/api/content/comments/{id}/disapprove/` | 管理员 | 拒绝 |

评论筛选：`content`、`author`、`search`。

评论字段：`content`、`user`、`parent`、`content_text`、`is_approved`。

## 4. 修订历史

`ContentRevision` 保存标题、正文、摘要的历史版本。
`GET /api/content/contents/{id}/revisions/` 返回该内容的修订列表。

## 5. 权限

| 操作 | 权限 |
|---|---|
| 浏览已发布内容/评论 | 公开 |
| 创建内容/评论 | 登录 |
| 编辑/删除内容 | 作者或管理员 |
| 提交审核 | 作者 |
| 审核/发布/撤回 | 管理员 |
| 查看草稿/被拒绝内容 | 作者或管理员 |

## 6. 积分

- 创建内容后按 `post` 规则异步发放 +10
- 评论走 `comment` 积分（+5）
- 内容被点赞的积分规则由互动模块统一处理

## 7. 前端与小程序

| 端 | 页面 |
|---|---|
| H5 | `Content`、`ContentCreate`、`ContentDetail` |
| 小程序 | `pages/content`、`pages/content-create`、`pages/content-detail` |

小程序支持草稿/提交审核/我的投稿状态筛选，与 H5 行为保持一致。
