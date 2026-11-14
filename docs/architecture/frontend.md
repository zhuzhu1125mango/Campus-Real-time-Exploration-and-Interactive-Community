# 前端架构（H5）

## 1. 技术栈

| 能力 | 选型 |
|---|---|
| 框架 | Vue 3（`<script setup>` + TypeScript） |
| 状态 | Pinia（组合式 store） |
| 路由 | Vue Router 4（History 模式） |
| UI | Element Plus、radix-vue、自定义 `components/common` |
| 样式 | UnoCSS + 原生 CSS |
| 请求 | Axios（统一封装） |
| 图表 | ECharts（按需引入） |
| 地图 | Leaflet |
| 富文本 | TinyMCE + DOMPurify |
| 构建 | Vite 6 |

## 2. 启动与外壳

入口链路：

```text
index.html
  → src/main.ts
    → createApp(App)
    → use(pinia)
    → use(ElementPlus)
    → 注册全部 Element Plus 图标
    → use(router)
    → mount('#app')
    → userStore.initialize()
```

`App.vue` 承担应用外壳：

- 启动时请求 `/health/` 判断后端可用性（带超时与重试）
- 已登录时加载用户信息
- 每 60 秒刷新未读私信数
- 顶部导航、通知下拉、主题切换、面包屑、返回顶部、页脚
- 通过 `<router-view>` 渲染页面

## 3. 目录结构

```text
frontend/src/
├── api/                 # 业务 API 封装
│   ├── user.ts / forum.ts / school.ts / learning.ts
│   └── content.ts / chat.ts / feed.ts / search.ts
├── components/          # 复用组件
│   └── common/          # TheButton / TheCard / TheInput / TheSearch
├── composables/         # useTheme / useToast
├── router/index.ts      # 路由与登录守卫
├── services/            # tokenExpiryService
├── stores/
│   ├── authStore.ts     # 登录/注册/登出
│   ├── tokenStore.ts    # 多账号 token 槽位
│   ├── userProfileStore.ts
│   └── userStore.ts     # 聚合门面
├── types/               # 与后端结构对应的类型
├── utils/
│   ├── request.ts       # Axios 实例与拦截器
│   ├── config.ts        # 运行时配置
│   ├── xss.ts           # v-html 清洗
│   ├── date.ts / image.ts / error.ts / logger.ts
│   └── echarts.ts       # 按需注册
├── views/               # 页面
├── App.vue
├── main.ts
└── style.css
```

## 4. 路由

集中在 `router/index.ts`：

- 使用 `createWebHistory(import.meta.env.BASE_URL)`
- 页面全部懒加载
- `meta.requiresAuth` 标记需要登录的页面
- 守卫逻辑：有 token 即放行，并在后台加载用户信息；无 token 跳转 `/login`

主要页面分组：

| 分组 | 页面 |
|---|---|
| 首页/探索 | `Home`、`Explore`、`Search` |
| 院校 | `Schools`、`SchoolDetail`、`SchoolList`、`MyFavoriteSchools` |
| 论坛 | `Forum`、`SchoolForum`、`BoardDetail`、`TopicDetail`、`TagDetail`、`PostDetail`、`Bookmarks` |
| 学习 | `Learning`、`CourseDetail`、`MyLearning` |
| 内容 | `Content`、`ContentCreate`、`ContentDetail` |
| 社交 | `Friends`、`Messages`、`ChatRoom`、`ChatDetail`、`UserProfile` |
| 用户 | `Login`、`Register`、`ResetPassword`、`Profile` |
| 其他 | `Activity`、`Events`、`Dashboard`、`NotificationsPage`、`ForumNotifications` |

## 5. 状态管理

四层拆分：

| Store | 职责 |
|---|---|
| `tokenStore` | 多账号 token 槽位、当前账号、刷新、切换 |
| `authStore` | 登录、注册、登出流程 |
| `userProfileStore` | 用户资料、收藏学校、积分 |
| `userStore` | 聚合门面，页面统一使用 |

Token 存储设计：

- 账号列表：`auth_accounts`
- 当前账号：`active_user_id`
- 每个账号的 token：`auth_tokens:<userId>`，值为 `{ access, refresh }`

这样可以支持同一浏览器切换多个账号，而不会互相覆盖。

## 6. 请求层

`utils/request.ts` 的关键行为：

1. 请求拦截器按当前账号注入 `Authorization: Bearer ...`。
2. 登录/刷新接口不注入旧 token。
3. 从 cookie 读取 `csrftoken` 并写入 `X-CSRFToken`。
4. 响应拦截器直接返回 `response.data`。
5. 401 时：
   - 登录与刷新请求直接失败，不重试
   - 其他请求只触发一次刷新，并发请求复用同一个 `refreshPromise`
   - 刷新失败清空全部 token 并跳转 `/login`
6. 其他状态码只做控制台提示，不改变 Promise 拒绝语义。

新增接口时：

```ts
// api/example.ts
import request from '@/utils/request'

export const exampleApi = {
  list(params: { page?: number }) {
    return request.get<{ results: unknown[]; count: number }>('/example/', { params })
  }
}
```

## 7. 安全

- 所有 `v-html` 必须使用 `utils/xss.ts` 过滤。
- 不在 `localStorage` 保存密码。
- 富文本编辑器上传内容由后端再次 `bleach` 清洗。
- 生产通过 Nginx 提供 HTTPS，避免 token 明文传输。

## 8. 构建与性能

`vite.config.ts` 关键配置：

- 别名：`@` → `src`，`@shared` → `../shared`
- 开发代理：`/api`、`/ws`、`/media`、`/health`
- `manualChunks` 拆分：echarts、element-plus、element-plus-icons、leaflet、vueuse、axios、pinia、vue-router、tinymce
- `chunkSizeWarningLimit: 1000`

ECharts 使用 `utils/echarts.ts` 按需注册图表与组件。

## 9. 实时通信

| 场景 | 文件 | 地址 |
|---|---|---|
| 公共聊天室 | `views/ChatRoom.vue` | `${wsBaseUrl}/ws/chat/public/` |
| 私信 | `components/ChatDetail.vue` | `${wsBaseUrl}/ws/chat/private/<userId>/` |

两者都包含心跳、断线重连、消息渲染与错误提示。协议见
[WebSocket 协议](../reference/websocket-protocol.md)。

## 10. 已知问题与技术债

- `utils/config.ts` 统一读取 `VITE_API_BASE_URL`、`VITE_WS_BASE_URL` 与 `VITE_MEDIA_BASE_URL`，缺省值适配本地代理。
- `Profile.vue` 体积较大（约 2300 行），后续可拆分为子组件。
- 没有前端单元测试框架；当前以 `pnpm type-check` 和手工回归为主。
- `Dashboard.vue`、`Content.vue` 等页面同时承担数据获取与展示，可逐步下沉到 composable。
