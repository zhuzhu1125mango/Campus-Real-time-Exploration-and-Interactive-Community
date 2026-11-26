import type { Page, Route } from '@playwright/test'

export interface MockApiOptions {
  /** 登录接口是否返回 401 */
  loginFails?: boolean
}

export const mockUser = {
  id: 1,
  username: 'e2e_user',
  email: 'e2e@example.com',
  avatar: '',
  bio: 'E2E 测试用户',
}

const mockTopic = {
  id: 1,
  title: 'E2E 测试主题',
  board: 1,
  board_name: '综合讨论',
  author: { id: 2, username: 'alice', avatar: '' },
  views: 12,
  reply_count: 3,
  post_count: 2,
  status: 'normal',
  tags: [],
  created_at: '2026-11-26T08:00:00Z',
  updated_at: '2026-11-26T09:00:00Z',
}

const mockFirstPost = {
  id: 11,
  topic: 1,
  is_first_post: true,
  content: '<p>这是首帖内容</p>',
  author: { id: 2, username: 'alice', avatar: '' },
  like_count: 0,
  is_liked: false,
  content_status: 'approved',
  created_at: '2026-11-26T08:00:00Z',
}

const paginated = <T,>(results: T[]) => ({
  count: results.length,
  next: null,
  previous: null,
  results,
})

const fulfillJson = (route: Route, body: unknown, status = 200) =>
  route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })

/**
 * 拦截全部 /api 请求，使用固定数据，避免测试依赖后端与数据库。
 */
export async function mockApi(page: Page, options: MockApiOptions = {}) {
  // 仅拦截 /api 前缀，避免误伤 /src/api/*.ts 等前端模块请求
  await page.route(
    (url) => url.pathname === '/api' || url.pathname.startsWith('/api/'),
    async (route) => {
      const request = route.request()
      const pathname = new URL(request.url()).pathname
      const method = request.method()

    if (pathname === '/api/health/') {
      return fulfillJson(route, { status: 'ok' })
    }

    if (pathname === '/api/users/users/login/' && method === 'POST') {
      return options.loginFails
        ? fulfillJson(route, { detail: '用户名或密码错误' }, 401)
        : fulfillJson(route, {
            access: 'e2e-access-token',
            refresh: 'e2e-refresh-token',
            user: mockUser,
          })
    }

    if (pathname === '/api/users/users/me/') {
      return fulfillJson(route, mockUser)
    }

    if (pathname === '/api/users/messages/unread_count/') {
      return fulfillJson(route, { unread_count: 0 })
    }
    if (pathname === '/api/users/notifications/count/') {
      return fulfillJson(route, { unread_count: 0 })
    }
    if (pathname === '/api/users/notifications/') {
      return fulfillJson(route, paginated([]))
    }
    if (pathname === '/api/users/friends/friend_list/') {
      return fulfillJson(route, { friends: [], count: 0 })
    }

    // 首页数据
    if (pathname === '/api/feed/feed/') {
      return fulfillJson(route, paginated([]))
    }
    if (pathname === '/api/feed/trending_topics/') {
      return fulfillJson(route, [])
    }
    if (pathname === '/api/schools/explore/nearby_places/') {
      return fulfillJson(route, [])
    }
    if (pathname === '/api/schools/explore/nearby_events/') {
      return fulfillJson(route, [])
    }
    if (pathname === '/api/schools/recommendations/') {
      return fulfillJson(route, { recommendations: [] })
    }
    if (pathname === '/api/learning/enrollments/') {
      return fulfillJson(route, paginated([]))
    }

    // 论坛数据
    if (pathname === '/api/topics/1/posts/') {
      return fulfillJson(route, paginated([mockFirstPost]))
    }
    if (pathname === '/api/topics/1/') {
      return fulfillJson(route, mockTopic)
    }
    if (pathname === '/api/topics/') {
      return fulfillJson(route, paginated([mockTopic]))
    }
    if (pathname === '/api/categories/') {
      return fulfillJson(route, [])
    }
    if (pathname === '/api/boards/') {
      return fulfillJson(route, paginated([]))
    }
    if (pathname === '/api/hot-topics/') {
      return fulfillJson(route, [])
    }
    if (pathname === '/api/tags/hot/') {
      return fulfillJson(route, [])
    }
    if (pathname === '/api/activities/') {
      return fulfillJson(route, paginated([]))
    }
    if (pathname === '/api/stats/') {
      return fulfillJson(route, {
        post_count: 0,
        today_post_count: 0,
        topic_count: 0,
        user_count: 0,
      })
    }

      // 兜底：GET 返回空分页，其余返回空对象，避免页面因异常数据崩溃
      if (method === 'GET') {
        return fulfillJson(route, paginated([]))
      }
      return fulfillJson(route, {})
    }
  )
}
