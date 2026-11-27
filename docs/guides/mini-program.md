# 小程序开发与对齐指南

小程序源码位于 `mp-weixin/`，基于 uni-app（Vue 3 `<script setup>`）。
使用 HBuilderX 打开该目录，或通过 uni-app CLI 构建为微信小程序。

环境变量见 `mp-weixin/.env.example`：

```env
VUE_APP_API_BASE_URL=https://api.example.com/api
VUE_APP_WS_BASE_URL=wss://api.example.com/ws/chat
```

## 1. 与 H5 功能对齐

### 1.1 已对齐

| 能力 | H5 | 小程序 |
|---|---|---|
| 登录/注册/重置密码 | ✅ | ✅ |
| 首页、探索、院校查询与详情 | ✅ | ✅ |
| 论坛、帖子详情、发主题 | ✅ | ✅ |
| 板块详情、标签聚合 | ✅ | ✅ |
| 学校专属论坛 | ✅ | ✅（院校详情进入板块详情） |
| 内容中心、详情、发布、草稿/审核 | ✅ | ✅ |
| 内容点赞、取消点赞、举报 | ✅ | ✅ |
| 搜索 | ✅ | ✅ |
| 公共聊天室、私信、撤回、输入中 | ✅ | ✅ |
| 好友列表、好友请求、添加好友 | ✅ | ✅ |
| 通知、收藏、我的学习 | ✅ | ✅ |
| 付费课程购买与课程证书 | ✅ | ✅ |
| 校园活动列表与报名 | ✅ | ✅ |
| 数据仪表盘 | ✅ | ✅（统计卡片 + 分布条，无 echarts） |
| 分享卡片与深链 | ✅ | ✅ |
| 订阅消息 | — | ✅ |

### 1.2 尚未对齐

| H5 页面 | 说明 |
|---|---|
| `TopicDetail.vue` | 小程序由 `pages/post-detail` 覆盖（首帖、回复、点赞、收藏、分享） |

## 2. 分享卡片与深链

以下页面已实现 `onShareAppMessage` 与 `onShareTimeline`：

| 页面 | 分享路径 |
|---|---|
| 首页 | `/pages/index/index` |
| 内容详情 | `/pages/content-detail/content-detail?id=<id>` |
| 帖子详情 | `/pages/post-detail/post-detail?id=<id>` |
| 院校详情 | `/pages/school-detail/school-detail?id=<id>` |
| 课程详情 | `/pages/course-detail/course-detail?id=<id>` |
| 用户资料 | `/pages/user-profile/user-profile?id=<id>` |

详情页均通过 `onLoad(options)` 读取 `id`，因此分享卡片、聊天转发与扫码进入
同一套深链逻辑。新增页面时请保持 `id` 作为主参数。

## 3. 订阅消息

### 3.1 后端配置

| 变量 | 说明 |
|---|---|
| `WECHAT_APPID` | 小程序 AppID |
| `WECHAT_SECRET` | 小程序 AppSecret |
| `WECHAT_TEMPLATE_COMMENT` | “新评论”模板 ID |
| `WECHAT_TEMPLATE_MESSAGE` | “新私信”模板 ID |
| `WECHAT_TEMPLATE_INTERACTION` | “点赞/好友请求”模板 ID |

模板字段约定为：`thing1`（标题）、`thing2`（内容，最多 20 字）、`time3`（时间）。
在微信公众平台创建模板时请使用对应字段名。

### 3.2 小程序配置

在 `mp-weixin/utils/wechat.js` 的 `SUBSCRIBE_TEMPLATE_IDS` 中填入同一批模板 ID：

```js
export const SUBSCRIBE_TEMPLATE_IDS = {
  comment: '模板ID',
  message: '模板ID',
  interaction: '模板ID'
}
```

### 3.3 流程

1. 用户登录后，小程序调用 `uni.login` 获取 code，并请求
   `POST /api/users/users/wechat_bind/` 绑定 openid。
2. 用户进入「我的 → 通知设置」，调用 `uni.requestSubscribeMessage` 授权模板；
   同意后调用 `POST /api/users/users/wechat_subscribe/` 记录授权。
3. 后端创建通知时，若接收者有 openid 且授权过对应模板，Celery 任务
   `send_wechat_subscribe_async` 会发送订阅消息。
4. 订阅消息为一次性授权：发送成功后消费对应模板授权，下次需用户重新授权。

### 3.4 微信一键登录

已提供 `POST /api/users/users/wechat_login/`：使用 `code` 换取 openid，
仅对已绑定账号返回 JWT；未绑定时返回 `need_bind=true`，引导用户先登录再绑定。

## 4. 排查

| 现象 | 排查 |
|---|---|
| 请求失败/域名不合法 | `VUE_APP_API_BASE_URL` 是否含 `/api`；生产必须 HTTPS 且在微信后台配置合法域名 |
| WebSocket 连不上 | `VUE_APP_WS_BASE_URL` 是否含 `/ws/chat`；token 通过 `jwt` 子协议传递 |
| 分享打开无数据 | 检查详情页 `onLoad` 是否读取 `id`，分享路径参数是否拼错 |
| 收不到订阅消息 | 检查模板 ID、字段名、用户是否授权；后端日志中搜索 `微信订阅消息` |
| 绑定失败 | 确认 AppID/Secret 正确，且该 openid 未被其他账号占用 |
