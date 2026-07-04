import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/userStore'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue')
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user/:id',
    name: 'UserProfile',
    component: () => import('../views/UserProfile.vue')
  },
  {
    path: '/user/me',
    name: 'MyProfile',
    component: () => import('../views/UserProfile.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/schools',
    name: 'Schools',
    component: () => import('@/views/Schools.vue')
  },
  {
    path: '/schools/:id',
    name: 'SchoolDetail',
    component: () => import('@/views/SchoolDetail.vue')
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('../views/ResetPassword.vue')
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('../views/NotificationsPage.vue'),
    meta: { requiresAuth: true }
  },
  // 论坛相关路由
  {
    path: '/forum',
    name: 'Forum',
    component: () => import('../views/Forum.vue')
  },
  {
    path: '/forum/:schoolId',
    name: 'SchoolForum',
    component: () => import('../views/SchoolForum.vue')
  },
  {
    path: '/forum/board/:boardId',
    name: 'BoardDetail',
    component: () => import('../views/BoardDetail.vue')
  },
  {
    path: '/forum/topic/:topicId',
    name: 'TopicDetail',
    component: () => import('../views/TopicDetail.vue')
  },
  {
    path: '/forum/tag/:tagId',
    name: 'TagDetail',
    component: () => import('../views/TagDetail.vue')
  },
  {
    path: '/forum/bookmarks',
    name: 'Bookmarks',
    component: () => import('../views/Bookmarks.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/forum/notifications',
    name: 'ForumNotifications',
    component: () => import('../views/ForumNotifications.vue'),
    meta: { requiresAuth: true }
  },
  {    path: '/my-favorite-schools',
    name: 'MyFavoriteSchools',
    component: () => import('../views/MyFavoriteSchools.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/chat/:id',
    name: 'ChatDetail',
    component: () => import('../components/ChatDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/messages',
    name: 'Messages',
    component: () => import('../views/Messages.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/chat-room',
    name: 'ChatRoom',
    component: () => import('../components/ChatRoom.vue')
  },
  {
    path: '/events',
    name: 'Events',
    component: () => import('../views/Events.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/friends',
    name: 'Friends',
    component: () => import('../views/Friends.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/learning',
    name: 'Learning',
    component: () => import('@/views/Learning.vue')
  },
  {
    path: '/learning/course/:courseId',
    name: 'CourseDetail',
    component: () => import('../views/CourseDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/my-learning',
    name: 'MyLearning',
    component: () => import('../views/MyLearning.vue'),
    meta: { requiresAuth: true }
  },
  // 内容中心路由
  {
    path: '/content',
    name: 'Content',
    component: () => import('../views/Content.vue')
  },
  {
    path: '/content/create',
    name: 'ContentCreate',
    component: () => import('../views/ContentCreate.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/content/:id',
    name: 'ContentDetail',
    component: () => import('../views/ContentDetail.vue')
  },
  {
    path: '/activity',
    name: 'Activity',
    component: () => import('../views/Activity.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫，检查登录状态
router.beforeEach(async (to, _from, next) => {
  const userStore = useUserStore()
  
  // 如果需要认证
  if (to.meta.requiresAuth) {
    // 检查是否有token
    if (userStore.token) {
      // 有token就允许访问，同时后台加载用户信息
      // 如果还没有用户信息，触发获取
      if (!userStore.user) {
        userStore.fetchUserInfo().catch(err => {
          console.error('获取用户信息失败:', err)
        })
      }
      next()
      return
    }
    
    // 如果没有token，重定向到登录页
    next('/login')
  } else {
    next()
  }
})

export default router 