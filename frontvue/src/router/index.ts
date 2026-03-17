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
  {
    path: '/my-favorite-schools',
    name: 'MyFavoriteSchools',
    component: () => import('../views/MyFavoriteSchools.vue'),
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
    // 检查是否已登录
    if (userStore.isLoggedIn) {
      next()
      return
    }
    
    // 如果有token但没有用户信息，尝试获取用户信息
    if (userStore.token && !userStore.user) {
      try {
        await userStore.fetchUserProfile()
        // 再次检查是否已登录
        if (userStore.isLoggedIn) {
          next()
          return
        }
      } catch (error) {
        console.error('获取用户信息失败:', error)
      }
    }
    
    // 如果以上条件都不满足，重定向到登录页
    next('/login')
  } else {
    next()
  }
})

export default router 