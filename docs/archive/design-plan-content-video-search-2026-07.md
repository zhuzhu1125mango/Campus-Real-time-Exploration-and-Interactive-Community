# 设计计划：Content 投稿 / 课时视频播放器 / 搜索优化

## 1. 目标与范围

基于当前已实现的后端模型和 H5 前端，本阶段重点补齐 **小程序端** 功能，同时确保 H5 端行为一致、后端无需大改。

| 模块 | 当前状态 | 本阶段目标 |
|------|---------|-----------|
| Content 用户投稿 | H5 完整；小程序仅支持直接发布 | 小程序支持草稿/提交审核/我的投稿状态管理 |
| 课时视频播放器 | H5 LessonPlayer 已支持续播、倍速、完成；小程序只有基础 video 标签 | 小程序播放器支持续播、倍速、进度保存、完成标记 |
| 搜索优化 | H5 全局搜索已完整；小程序无搜索页面 | 小程序新增全局搜索页及入口 |

## 2. Content 用户投稿

### 2.1 问题分析
- 小程序 `content-create.vue` 直接提交 `is_published: true`，未走审核流程。
- 小程序缺少 `submitContent`、`getMyContents` API 及对应页面状态筛选。
- 小程序内容列表没有展示/筛选用户自己内容的状态标签。

### 2.2 改动内容

#### 后端（已具备，仅做兼容性微调）
- `ContentViewSet.submit/approve/reject/my_contents` 已存在，`Content.status` 与 `is_published` 自动同步。
- 无需新增模型或迁移。

#### 小程序 API（`mp-weixin/api/content.js`）
- 新增 `submitContent(id)`：调用 `POST /content/contents/{id}/submit/`。
- 新增 `getMyContents(params)`：调用 `GET /content/contents/my_contents/?status=xxx`。
- 新增 `updateContent(id, data)`、`deleteContent(id)`，用于作者后续管理。

#### 小程序页面
- `pages/content/content.vue`
  - 顶部新增 Tab：全部 / 我的投稿 / 草稿 / 待审核 / 已拒绝。
  - 登录用户切换 Tab 时调用 `getMyContents`。
  - 内容卡片上显示状态标签（仅在我的投稿相关 Tab 下）。
- `pages/content-create/content-create.vue`
  - 提交表单时增加发布方式选择：保存草稿 / 提交审核。
  - 不再传 `is_published: true`；草稿传 `status=draft`，提交审核传 `status=pending`。
  - 已发布内容编辑时，仅作者/管理员可操作。
- `pages/content-detail/content-detail.vue`
  - 内容头部显示状态标签。
  - 作者本人可见操作区：编辑、删除、提交审核（草稿/拒绝状态）、撤回为草稿（待审核状态）。

#### H5（可选一致性增强）
- `frontend/src/views/ContentCreate.vue`：按钮文案明确区分为「保存草稿」与「提交审核」。
- `frontend/src/views/ContentDetail.vue`：作者可见状态与操作按钮（编辑、删除、提交/撤回）。

### 2.3 验收标准
1. 小程序游客只能看到已发布内容。
2. 登录用户在小程序可创建草稿或提交审核。
3. 作者可在小程序查看自己的草稿/待审核/已拒绝内容，并执行提交/撤回/删除。
4. 管理员在 Django Admin 中审批后，内容状态变为已发布，所有用户可见。

## 3. 课时视频播放器增强

### 3.1 问题分析
- 小程序 `pages/course-detail/course-detail.vue` 仅使用原生 `<video>` 弹窗播放，无进度记忆、倍速、完成同步。
- 后端 `Progress.last_position` 已存在，`recordProgress` 接口已就绪。

### 3.2 改动内容

#### 后端（无需改动）
- `ProgressViewSet.record` 支持创建/更新进度，自动更新课程总体进度。
- `LessonViewSet.increment_view` 已存在。

#### 小程序 API（已具备）
- `learningApi.recordProgress({ enrollment, lesson, last_position, is_completed })` 已存在。
- `learningApi.incrementLessonView(lessonId)` 已存在。

#### 小程序页面（`pages/course-detail/course-detail.vue`）
- 新增播放器状态：
  - `currentLesson`、`playerVisible`、`enrollment`。
  - `lessonProgress`：当前课时进度缓存。
- 打开课时播放器时：
  - 查询当前 `enrollment` 与课时的 `Progress`。
  - 若不存在则调用 `recordProgress` 创建一条默认记录。
- 视频播放期间：
  - 使用 `video` 组件的 `@timeupdate` 事件，每 10 秒或进度变化较大时调用 `recordProgress` 保存 `last_position`。
  - 提供倍速选择按钮（0.5x / 0.75x / 1.0x / 1.25x / 1.5x / 2.0x），通过 `playbackRate` 属性设置。
- 视频播放结束：
  - 自动调用 `recordProgress` 标记 `is_completed=true`，刷新课时列表完成状态。
  - 自动播放下一个可观看课时。
- 课时列表项：
  - 显示已完成/未完成状态图标。

#### H5
- `frontend/src/components/LessonPlayer.vue` 已具备上述能力，本阶段仅做回归验证，不改动主要逻辑。

### 3.3 验收标准
1. 小程序已报名用户打开课时，自动从上次观看位置继续播放。
2. 播放过程中进度被定时保存，刷新页面后可恢复。
3. 用户可切换倍速，倍速设置在当前课时生效。
4. 视频播放结束后，该课时标记为已完成，并自动进入下一课时。
5. 未报名用户点击非免费课时提示报名。

## 4. 搜索优化

### 4.1 问题分析
- H5 全局搜索已支持课程、内容、学校、论坛主题、帖子。
- 小程序没有搜索页面和搜索入口。

### 4.2 改动内容

#### 后端（无需改动）
- `search/views.py` 的 `global_search` 与 `search_suggestions` 已支持所需类型。

#### 小程序 API（新增 `mp-weixin/api/search.js`）
- `search(q, type, limit)`：调用 `GET /search/?q=&type=&limit=`。
- `getSuggestions(q)`：调用 `GET /search/suggestions/?q=`。

#### 小程序页面（新增 `pages/search/search.vue`）
- 顶部搜索栏：输入框 + 搜索按钮，支持搜索建议下拉。
- 分类 Tab：全部 / 课程 / 内容 / 学校 / 论坛主题 / 帖子。
- 结果列表按类型分块展示，点击跳转对应详情页：
  - 课程 → `/pages/course-detail/course-detail?id=`
  - 内容 → `/pages/content-detail/content-detail?id=`
  - 学校 → `/pages/school-detail/school-detail?id=`
  - 论坛主题 → `/pages/post-detail/post-detail?id=`（或后续新增的主题详情页）
  - 帖子 → `/pages/post-detail/post-detail?id=`

#### 小程序入口
- `pages/index/index.vue`：顶部导航区增加搜索入口，点击跳转搜索页。
- `pages/content/content.vue`、`pages/learning/learning.vue`：搜索框点击跳转搜索页并带默认类型。

#### 小程序配置
- `pages.json` 注册 `pages/search/search` 页面。

#### H5（可选优化）
- `frontend/src/views/Search.vue`：搜索结果关键词高亮、空状态优化、分页加载（当前为一次性 limit）。

### 4.3 验收标准
1. 小程序首页可通过搜索入口进入搜索页。
2. 输入关键词后返回课程/内容/学校/主题/帖子结果。
3. 切换类型 Tab 可筛选结果。
4. 点击建议或结果项可正确跳转到详情页。

## 5. 开发顺序

1. **Content 用户投稿**（小程序 API + 列表/创建/详情页）
2. **课时视频播放器增强**（小程序 course-detail 播放器重构）
3. **搜索优化**（小程序搜索页 + 入口）
4. **联调与验证**（H5 回归 + 小程序真机/模拟器验证）

## 6. 涉及主要文件

### 小程序
- `mp-weixin/api/content.js`
- `mp-weixin/api/search.js`（新增）
- `mp-weixin/pages/content/content.vue`
- `mp-weixin/pages/content-create/content-create.vue`
- `mp-weixin/pages/content-detail/content-detail.vue`
- `mp-weixin/pages/course-detail/course-detail.vue`
- `mp-weixin/pages/search/search.vue`（新增）
- `mp-weixin/pages/index/index.vue`
- `mp-weixin/pages/learning/learning.vue`
- `mp-weixin/pages.json`

### H5
- `frontend/src/views/ContentCreate.vue`
- `frontend/src/views/ContentDetail.vue`
- `frontend/src/views/Search.vue`

### 后端
- 预计无需模型迁移或新增视图；仅可能修复验证过程中的小 bug。

## 7. 风险与备注
- 小程序 `<video>` 组件在不同平台的倍速支持存在差异，需在微信开发者工具/真机验证。
- 小程序富文本内容通过 `<rich-text>` 渲染，投稿时仅支持简单 HTML。
- 搜索的论坛主题当前无独立小程序详情页，暂时跳转帖子详情或后续再补充主题页。
