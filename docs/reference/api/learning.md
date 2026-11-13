# 学习 API

前缀：`/api/learning/`。

## 1. 课程分类

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/learning/categories/` | 读公开/写管理员 | 分类列表/创建 |
| GET/PATCH/PUT/DELETE | `/api/learning/categories/{id}/` | 读公开/管理员写 | 分类详情/管理 |

## 2. 课程

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/api/learning/courses/` | 公开 | 课程列表 |
| POST | `/api/learning/courses/` | 登录（讲师/管理员） | 创建课程 |
| GET | `/api/learning/courses/{id}/` | 公开 | 课程详情 |
| PATCH/PUT/DELETE | `/api/learning/courses/{id}/` | 讲师/管理员 | 更新/删除 |
| POST | `/api/learning/courses/{id}/publish/` | 讲师/管理员 | 发布 |
| POST | `/api/learning/courses/{id}/unpublish/` | 讲师/管理员 | 取消发布 |
| GET | `/api/learning/courses/{id}/chapters/` | 公开 | 章节列表 |
| GET | `/api/learning/courses/{id}/lessons/` | 公开 | 课时列表 |
| GET | `/api/learning/courses/{id}/resources/` | 公开 | 学习资源 |
| GET | `/api/learning/courses/{id}/reviews/` | 公开 | 课程评价 |

课程列表参数：

| 参数 | 说明 |
|---|---|
| `category` | 分类 ID |
| `is_free` | `true`/`false` |
| `search` | 标题/描述搜索 |
| `page` / `page_size` | 分页 |

课程字段：`title`、`slug`、`description`、`instructor`、`cover_image`、
`price`、`is_free`、`is_published`、`publish_date`、`enroll_count`、
`view_count`、`average_rating`。

规则：

- 只有已发布课程对普通用户可见
- `is_published=True` 时自动补 `publish_date`
- 创建课程发放积分（`create_course`）

## 3. 章节与课时

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/learning/chapters/` | 读公开/写讲师 | 章节列表/创建 |
| GET/PATCH/PUT/DELETE | `/api/learning/chapters/{id}/` | 读公开/讲师 | 章节详情/管理 |
| GET | `/api/learning/chapters/{id}/lessons/` | 公开 | 章节下课时 |
| GET/POST | `/api/learning/lessons/` | 读公开/写讲师 | 课时列表/创建 |
| GET/PATCH/PUT/DELETE | `/api/learning/lessons/{id}/` | 读公开/讲师 | 课时详情/管理 |
| POST | `/api/learning/lessons/{id}/increment_view/` | 公开 | 增加观看次数 |

课时字段：`title`、`description`、`content`、`video_url`、`duration`、
`is_free`、`order`、`view_count`。

## 4. 报名

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/learning/enrollments/` | 登录 | 我的报名/报名课程 |
| GET/PATCH/PUT/DELETE | `/api/learning/enrollments/{id}/` | 本人/管理员 | 报名详情/管理 |
| POST | `/api/learning/enrollments/{id}/complete/` | 本人 | 完成课程 |
| GET | `/api/learning/enrollments/{id}/progress/` | 本人 | 学习进度 |

报名规则：

- `unique_together = (user, course)`，重复报名返回校验错误
- 免费课程直接报名；付费课程当前无支付流程
- 报名后按 `favorite` 规则异步发放 +2（沿用现有实现）
- 完成课程发放 `complete_course` 积分（+20）

## 5. 学习进度

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/learning/progresses/` | 登录 | 进度列表/创建 |
| GET/PATCH/PUT/DELETE | `/api/learning/progresses/{id}/` | 本人 | 进度详情/更新 |
| POST | `/api/learning/progresses/record/` | 登录 | 记录播放进度（推荐） |

`record` body：

```json
{
  "enrollment": 1,
  "lesson": 10,
  "last_position": 120,
  "is_completed": false
}
```

行为：

- 不存在则创建，存在则更新
- 更新 `last_watched_at`
- 重新计算课程总体 `progress`
- 课时完成时可触发课程完成判断

## 6. 评价

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/learning/reviews/` | 读公开/写登录 | 评价列表/创建 |
| GET/PATCH/PUT/DELETE | `/api/learning/reviews/{id}/` | 本人/管理员 | 评价管理 |
| POST | `/api/learning/reviews/{id}/approve/` | 管理员 | 通过 |
| POST | `/api/learning/reviews/{id}/disapprove/` | 管理员 | 拒绝 |

规则：

- `rating` 为 1–5
- `unique_together = (user, course)`
- 只有 `is_approved=True` 的评价参与平均分展示

## 7. 学习资源

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/learning/resources/` | 读公开/写讲师 | 资源列表/上传 |
| GET/PATCH/PUT/DELETE | `/api/learning/resources/{id}/` | 读公开/讲师 | 资源管理 |
| POST | `/api/learning/resources/{id}/increment_download/` | 登录 | 增加下载次数 |

资源字段：`title`、`description`、`file`、`file_type`、`file_size`、
`download_count`、`is_free`。

## 8. 权限

| 操作 | 权限 |
|---|---|
| 浏览课程/章节/课时/评价 | 公开 |
| 创建/编辑课程、章节、课时、资源 | 讲师本人或管理员 |
| 报名、记录进度、评价 | 登录 |
| 审核评价 | 管理员 |
| 发布/取消发布 | 讲师或管理员 |

## 9. 前端与小程序

- H5：`Learning`、`CourseDetail`、`MyLearning`、`LessonPlayer`
- 小程序：`pages/learning`、`pages/course-detail`、`pages/my-learning`

小程序播放器支持续播、倍速、进度保存与完成标记；H5 对应能力在
`components/LessonPlayer.vue`。
