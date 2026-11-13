# Feed 与搜索 API

## 1. Feed

前缀：`/api/feed/`。

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/api/feed/feed/` | 公开 | 聚合 Feed |
| GET | `/api/feed/trending_topics/` | 公开 | 热门标签/话题 |

### 1.1 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `type` | `recommend` | `recommend` / `following` / `nearby` |
| `page` | 1 | 页码 |
| `page_size` | 10 | 每页数量 |
| `lat` / `lng` | 无 | `nearby` 必填 |
| `radius` | 10 | `nearby` 半径，0.1–50 km |

### 1.2 类型

| 类型 | 数据来源 |
|---|---|
| `recommend` | 近 30 天论坛主题、已发布内容、公开动态 |
| `following` | 好友（`Friend`）的主题/内容/动态 |
| `nearby` | 附近学校的地点 → 这些学校即将开始/进行中的公开活动 |

### 1.3 响应

```json
{
  "results": [
    {
      "id": "topic_1",
      "object_type": "topic",
      "object_id": 1,
      "title": "标题",
      "content": "正文",
      "author": {"id": 1, "username": "alice", "avatar": null},
      "images": [],
      "meta": {
        "board_name": "校园生活",
        "reply_count": 3,
        "view_count": 100
      },
      "created_at": "2026-11-13T10:00:00+08:00"
    }
  ],
  "count": 1,
  "page": 1,
  "page_size": 10,
  "type": "recommend"
}
```

`object_type` 取值：`topic`、`content`、`activity`、`event`。

### 1.4 热门标签

```http
GET /api/feed/trending_topics/
```

返回合并后的论坛标签与内容标签：

```json
[
  {
    "id": "forum_tag_1",
    "type": "forum_tag",
    "name": "考研",
    "description": "",
    "count": 12
  }
]
```

按关联数量倒序取前 15 条。

## 2. 搜索

前缀：`/api/search/`。

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/api/search/?q=&type=&limit=` | 公开 | 全局聚合搜索 |
| GET | `/api/search/suggestions/?q=` | 公开 | 搜索建议 |

### 2.1 全局搜索

| 参数 | 默认 | 说明 |
|---|---|---|
| `q` | 空 | 关键词，空查询返回空结果 |
| `type` | `all` | `all` / `course` / `content` / `school` / `topic` / `post` / `user` |
| `limit` | 10 | 每类数量，最大 50 |

响应：

```json
{
  "query": "计算机",
  "type": "all",
  "results": {
    "courses": [],
    "contents": [],
    "schools": [],
    "topics": [],
    "posts": [],
    "users": []
  }
}
```

说明：

- `type=all` 时返回全部分组；指定类型时只返回对应分组
- 用户搜索对普通用户只返回公开字段；管理员可包含更多信息
- 优先 Elasticsearch + ik；ES 不可用时降级 MySQL `LIKE`

### 2.2 搜索建议

```http
GET /api/search/suggestions/?q=计
```

响应：

```json
{
  "query": "计",
  "suggestions": [
    {"type": "school", "id": 1, "title": "XX大学", "slug": null}
  ]
}
```

规则：

- 每类最多 5 条
- 空查询返回空数组
- 同样支持 ES 与数据库降级

## 3. 与论坛搜索的区别

| 场景 | 接口 | 说明 |
|---|---|---|
| 全站聚合搜索 | `/api/search/` | 跨模块，适合顶部搜索框 |
| 论坛内搜索 | `/api/topics/?search=`、`/api/posts/?search=` | 论坛列表过滤 |
| 学校内搜索 | `/api/schools/?search=` | 学校列表过滤 |
| 标签建议 | `/api/feed/trending_topics/` | 热门标签，不是关键词搜索 |

## 4. 性能与降级

- ES 查询返回 id 后回表 ORM，保证返回结构与列表接口一致
- ES 不可用时自动走 `icontains`，响应结构不变
- 搜索接口受 `SearchThrottle` 限制（30/min）
