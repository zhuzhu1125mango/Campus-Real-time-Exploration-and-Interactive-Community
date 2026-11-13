# 数据模型

本文列出当前代码中的业务模型、表名与关键字段。字段类型以 Django 模型为准，
迁移文件位于各 app 的 `migrations/`。

## 1. 领域关系

```text
User ──1:1── UserProfile
  │
  ├──1:N── PointsRecord / UserActivity / ChatMessage
  ├──M:N── favorite_schools ── School
  ├──M:N── following (self)
  ├──1:N── Topic / Post / Comment
  ├──1:N── Enrollment ── Course
  ├──1:N── Favorite (ContentType 多态)
  ├──1:1/M:N── FriendRequest / Friend
  └──1:N── Notification (recipient/sender)

School ──1:1── Board
  ├──1:N── SchoolMajor ── Major
  ├──1:N── AdmissionScore / SchoolRating / Event / Place
  └──1:N── EventRegistration ── Event

Course ──1:N── Chapter ──1:N── Lesson
  ├──1:N── Enrollment ──1:N── Progress
  ├──1:N── Review
  └──1:N── LearningResource

Content ──1:N── Comment / ContentRevision
  └──M:N── Tag
```

## 2. 用户与积分（`users`）

### User → `users_user`

继承 `AbstractUser`，扩展字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `email` | Email | 唯一，可空 |
| `phone` | Char(11) | 唯一，可空 |
| `avatar` / `banner` | Image | 带头像/横幅校验 |
| `gender` | Char(1) | `M`/`F`/`O` |
| `school` / `major` / `grade` | Char | 教育信息 |
| `bio` | Text | 入库前 HTML 清洗 |
| `is_verified` | Bool | 验证码通过后置位 |
| `points` / `level` | Int | 积分与等级 |
| `favorite_schools` | M2M School | 收藏学校 |
| `following` | M2M self | 关注关系 |

### UserProfile → `users_userprofile`

`user` 一对一；`interests`、`target_schools`、`target_majors`、`gpa`、
`study_status`、`website`、`social_links`。

### VerificationCode → `users_verificationcode`

`code`、`email`/`phone`、`code_type`（email/phone/password）、
`is_used`、`expires_at`；含 email/phone/created_at 索引。

### UserActivity → `users_useractivity`

`user`、`activity_type`、`target_type`、`target_id`、`metadata`、`timestamp`。

### PointsRecord → `users_pointsrecord`

`user`、`action`、`points`、`description`、`created_at`。
用于积分流水与幂等判断。

## 3. 论坛（`forum`）

| 模型 | 表 | 关键字段 |
|---|---|---|
| `Category` | `forum_category` | `name`、`order` |
| `Board` | `forum_board` | `category`、`name`、`school`（OneToOne）、`moderators`（M2M User） |
| `Topic` | `forum_topic` | `board`、`title`、`author`、`status`、`views`、`is_closed` |
| `Post` | `forum_post` | `topic`、`author`、`content`、`is_first_post`、`content_status`、审核字段 |
| `Attachment` | `forum_attachment` | `post`、`file`、`filename`、`file_size`、`file_type` |
| `Like` | `forum_like` | `post`、`user`（唯一） |
| `Tag` | `forum_tag` | `name`（唯一）、`topics`（M2M） |
| `Report` | `forum_report` | `reporter`、`post`、`report_type`、`status` |
| `Bookmark` | `forum_bookmark` | `user`、`topic`（唯一） |
| `Comment` | `forum_comment` | `post`、`author`、`content`、`parent`（自关联） |
| `CommentLike` | `forum_commentlike` | `comment`、`user`（唯一） |

## 4. 院校（`schools`）

| 模型 | 表 | 关键字段 |
|---|---|---|
| `School` | `schools_school` | `name`、`english_name`、`code`、`school_type`、`school_level`、`province`、`city`、`national_rank` |
| `Major` | `schools_major` | `name`、`code`、`degree_type`、`subject_category` |
| `SchoolMajor` | `schools_schoolmajor` | `school`、`major`、`is_key_major`、`is_characteristic_major` |
| `SchoolRating` | `schools_schoolrating` | `school`、`user`、`rating`、`comment`（唯一 user+school） |
| `MajorRating` | `schools_majorrating` | `major`、`user`、`rating`、`comment` |
| `AdmissionScore` | `schools_admissionscore` | `school`、`major`、`year`、`province`、`score_type`、`min_score`、`avg_score` |
| `Event` | `schools_event` | `school`、`title`、`start_time`、`end_time`、`location`、`status`、`is_public` |
| `EventRegistration` | `schools_eventregistration` | `event`、`user`、`status`、`metadata`（唯一 event+user） |
| `Place` | `schools_place` | `school`、`name`、`category`、`latitude`、`longitude`、`checkin_count` |
| `CheckIn` | `schools_checkin` | `user`、`place`、`latitude`、`longitude`、`note` |

索引：

- 学校：`province`、`school_type`、`school_level`、`-national_rank`
- 分数线：`school + -year`、`province + -year`
- 活动：`school + start_time`、`status + start_time`
- 地点：`school + category`、`latitude + longitude`
- 打卡：`user + -created_at`、`place + -created_at`

## 5. 学习（`learning`）

| 模型 | 表 | 关键字段 |
|---|---|---|
| `Course` | `learning_course` | `title`、`slug`（唯一）、`instructor`、`price`、`is_free`、`is_published`、`enroll_count`、`average_rating` |
| `Category` | `learning_category` | `name`（唯一）、`parent`、`order` |
| `CourseCategory` | `learning_coursecategory` | `course`、`category`（唯一） |
| `Chapter` | `learning_chapter` | `course`、`title`、`order` |
| `Lesson` | `learning_lesson` | `chapter`、`title`、`video_url`、`duration`、`is_free`、`view_count` |
| `Enrollment` | `learning_enrollment` | `user`、`course`、`is_completed`、`progress`（唯一 user+course） |
| `Progress` | `learning_progress` | `enrollment`、`lesson`、`is_completed`、`last_position`（唯一 enrollment+lesson） |
| `Review` | `learning_review` | `user`、`course`、`rating`、`comment`、`is_approved`（唯一 user+course） |
| `LearningResource` | `learning_learningresource` | `course`、`file`、`file_type`、`file_size`、`download_count` |

## 6. 内容（`content`）

| 模型 | 表 | 关键字段 |
|---|---|---|
| `ContentType` | `content_contenttype` | `name`（唯一）、`is_active` |
| `Category` | `content_category` | `name`（唯一）、`parent`、`order` |
| `Tag` | `content_tag` | `name`（唯一） |
| `Content` | `content_content` | `title`、`slug`（唯一）、`content_type`、`category`、`author`、`content`、`summary`、`status`、`is_published`、`publish_date`、计数 |
| `Comment` | `content_comment` | `content`、`user`、`parent`、`content_text`、`is_approved` |
| `ContentRevision` | `content_contentrevision` | `content`、`author`、`title`、`content_text`、`summary` |

## 7. 社交（`activities` / `favorites` / `friendships` / `private_messages`）

| 模型 | 表 | 关键字段 |
|---|---|---|
| `Activity` | `users_activity` | `user`、`activity_type`、`content`、`target_*`、`is_public`、计数 |
| `ActivityLike` | `users_activitylike` | `activity`、`user`（唯一） |
| `ActivityComment` | `users_activitycomment` | `activity`、`user`、`content`、`parent` |
| `Favorite` | `users_favorite` | `user`、`content_type`、`object_id`、`category`、`note`、`content_object`（GenericFK） |
| `FriendRequest` | `users_friendrequest` | `sender`、`receiver`、`status` |
| `Friend` | `users_friend` | `user1`、`user2` |
| `Message` | `users_message` | `sender`、`receiver`、`content`、`is_read` |

## 8. 聊天与通知（`chat` / `notifications`）

| 模型 | 表 | 关键字段 |
|---|---|---|
| `ChatMessage` | `chat_chatmessage` | `user`（可空）、`content`、`created_at` |
| `Notification` | `users_notification` | `recipient`、`sender`、`notification_type`、`title`、`content`、`content_type`/`object_id`、`url`、`is_read` |

通知类型：`system`、`interaction`、`content_comment`、`message`、`activity`。

## 9. 表命名说明

部分模型保留历史表名：

- `activities.Activity` → `users_activity`（原 users app）
- `favorites.Favorite` → `users_favorite`
- `friendships.FriendRequest` → `users_friendrequest`
- `private_messages.Message` → `users_message`
- `notifications.Notification` → `users_notification`

这是为了兼容旧数据迁移，新增模型应使用默认 `<app>_<model>` 表名。

## 10. 维护要求

新增/修改模型时同步更新：

1. 迁移文件
2. 本文件
3. 对应 API 文档
4. 搜索文档（如果参与全局搜索）
5. 前端/小程序类型定义
6. Admin 注册
