# 院校 API

前缀：`/api/schools/`。

## 1. 学校

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/api/schools/` | 公开 | 学校列表（缓存） |
| POST | `/api/schools/` | 管理员 | 创建学校 |
| GET | `/api/schools/{id}/` | 公开 | 学校详情 |
| PATCH/PUT | `/api/schools/{id}/` | 管理员 | 更新 |
| DELETE | `/api/schools/{id}/` | 管理员 | 删除 |
| GET | `/api/schools/{id}/majors/` | 公开 | 学校专业 |
| GET | `/api/schools/{id}/admission_scores/` | 公开 | 录取分数线 |
| GET | `/api/schools/{id}/ratings/` | 公开 | 学校评价 |
| POST | `/api/schools/{id}/rate/` | 登录 | 评价学校 |
| POST | `/api/schools/{id}/favorite/` | 登录 | 收藏 |
| POST | `/api/schools/{id}/unfavorite/` | 登录 | 取消收藏 |
| GET | `/api/schools/{id}/forums/` | 公开 | 学校论坛板块（不存在时自动创建） |
| POST | `/api/schools/compare/` | 公开 | 院校对比 |
| POST | `/api/schools/import_csv/` | 管理员 | CSV 导入 |
| GET | `/api/schools/favorite-schools/` | 登录 | 我收藏的学校 |
| POST | `/api/schools/log-activity/` | 公开 | 记录用户行为 |
| GET | `/api/schools/recommendations/` | 公开 | 推荐 |
| GET | `/api/schools/test-connection/` | 公开 | 连通性检查 |

### 1.1 列表参数

| 参数 | 说明 |
|---|---|
| `province` | 省份 |
| `school_type` | 学校类型 |
| `school_level` | 办学层次 |
| `search` | 关键词，优先 ES，失败降级 LIKE |
| `sort_by` | `ranking` / `name` / `founded_year` |
| `page` / `page_size` | 分页 |

学校类型：`comprehensive`、`science`、`liberal_arts`、`medical`、
`agriculture`、`normal`、`finance`、`engineering`、`other`。

办学层次：`985`、`211`、`double_first_class`、`key`、`ordinary`。

### 1.2 对比

```http
POST /api/schools/compare/
Content-Type: application/json

{
  "school_ids": [1, 2, 3],
  "comparison_fields": ["national_rank", "student_count"]
}
```

规则：

- 2–4 所学校
- 学校必须全部存在
- 结果按对比维度聚合

### 1.3 评价

```http
POST /api/schools/{id}/rate/
Authorization: Bearer <access>
Content-Type: application/json

{"rating": 5, "comment": "环境很好"}
```

- `rating` 必须为 1–5 的整数
- 同一用户对同一学校重复评价会更新原记录

### 1.4 推荐

```http
GET /api/schools/recommendations/?type=schools&limit=10
```

`type` 由 `schools/recommendation.py` 决定推荐策略，`limit` 为返回数量。

## 2. 专业

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/schools/majors/` | 读公开/写管理员 | 专业列表/创建 |
| GET/PATCH/PUT/DELETE | `/api/schools/majors/{id}/` | 读公开/管理员写 | 专业详情/管理 |
| GET | `/api/schools/majors/{id}/schools/` | 公开 | 开设该专业的学校 |
| GET | `/api/schools/majors/{id}/ratings/` | 公开 | 专业评价 |
| POST | `/api/schools/majors/{id}/rate/` | 登录 | 评价专业 |

专业列表参数：`search`、`degree_type`、`subject_category`。

学位类型：`bachelor`、`master`、`doctor`。

学科门类：`philosophy`、`economics`、`law`、`education`、`literature`、
`history`、`science`、`engineering`、`agriculture`、`medicine`、
`management`、`art`。

## 3. 录取分数线

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/schools/admission-scores/` | 读公开/写管理员 | 列表/创建 |
| GET/PATCH/PUT/DELETE | `/api/schools/admission-scores/{id}/` | 读公开/管理员写 | 详情/管理 |

筛选参数：`school_id`、`major_id`、`year`、`province`、`score_type`。

`score_type`：`science`（理科）、`liberal_arts`（文科）、`comprehensive`（综合）。

## 4. 校园活动

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/schools/events/` | 读公开/写管理员 | 活动列表/创建 |
| GET/PATCH/PUT/DELETE | `/api/schools/events/{id}/` | 读公开/管理员写 | 活动详情/管理 |
| POST | `/api/schools/events/{id}/register/` | 登录 | 报名 |
| POST | `/api/schools/events/{id}/cancel_registration/` | 登录 | 取消报名 |
| GET/POST | `/api/schools/event-registrations/` | 登录/管理员 | 报名记录 |
| GET/PATCH/PUT/DELETE | `/api/schools/event-registrations/{id}/` | 本人/管理员 | 报名记录管理 |

活动筛选：`school_id`、`start_date`、`end_date`、`status`、`page`、`page_size`。

活动状态：`upcoming`、`ongoing`、`completed`、`cancelled`。
报名状态：`pending`、`confirmed`、`cancelled`。

## 5. 校园探索

`ExploreViewSet` 提供地图探索能力。

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/api/schools/explore/places/` | 公开 | 按学校/分类查地点 |
| GET | `/api/schools/explore/nearby_places/` | 公开 | 附近地点 |
| GET | `/api/schools/explore/nearby_events/` | 公开 | 附近活动 |
| POST | `/api/schools/explore/checkin/` | 登录 | 地点打卡 |
| GET | `/api/schools/explore/my_checkins/` | 登录 | 我的打卡记录 |

参数：

| 接口 | 参数 |
|---|---|
| `places` | `school_id`、`category` |
| `nearby_places` | `lat`、`lng`、`radius`（km，0.1–50，默认 5）、`school_id`、`category` |
| `nearby_events` | `lat`+`lng`+`radius`，或 `school_id` |
| `checkin` | body `place_id`、`latitude`、`longitude`、`note` |

规则：

- 附近地点使用矩形预筛 + Haversine 精确距离，按距离升序
- 同一用户同一地点每天只能打卡一次
- 地点分类：`landmark`、`building`、`dormitory`、`canteen`、`library`、
  `sport`、`activity`、`scenic`、`other`

## 6. 元数据

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/schools/provinces/` | 省份列表 |
| GET | `/api/schools/cities/?province=` | 城市列表 |
| GET | `/api/schools/types/` | 学校类型 |
| GET | `/api/schools/levels/` | 办学层次 |
| GET | `/api/schools/major-types/` | 学位类型 |
| GET | `/api/schools/subject-categories/` | 学科门类 |

## 7. 统计

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/schools/stats/school/` | 学校统计 |
| GET | `/api/schools/stats/forum/` | 论坛统计 |
| GET | `/api/schools/stats/event/` | 活动统计 |
| GET | `/api/schools/stats/user/` | 用户统计 |
| GET | `/api/schools/stats/dashboard/` | 仪表盘汇总 |

统计实现位于 `schools/stats.py`，部分结果会缓存。

## 8. 缓存与降级

- 学校列表与对比结果使用统一缓存层
- 搜索优先 Elasticsearch，失败后降级为 `icontains`
- 缓存 key 前缀由 `CACHE_KEY_PREFIX` 控制

## 9. 权限

- 浏览、对比、推荐：公开
- 评价、收藏、打卡、报名：登录
- 创建/更新/删除学校、专业、分数线、活动：管理员
- CSV 导入：管理员
