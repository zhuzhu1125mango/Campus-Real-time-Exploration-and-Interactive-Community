<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

interface Crumb {
  label: string
  to?: string
}

const route = useRoute()
const router = useRouter()

const titleMap: Record<string, string> = {
  Home: '首页',
  Login: '登录',
  Register: '注册',
  Profile: '个人中心',
  UserProfile: '用户主页',
  MyProfile: '我的主页',
  Explore: '校园探索',
  Schools: '院校查询',
  SchoolDetail: '院校详情',
  ResetPassword: '重置密码',
  Notifications: '通知中心',
  Forum: '论坛',
  SchoolForum: '院校论坛',
  BoardDetail: '版块详情',
  TopicDetail: '话题详情',
  TagDetail: '标签详情',
  Bookmarks: '我的收藏',
  ForumNotifications: '论坛通知',
  MyFavoriteSchools: '收藏院校',
  ChatRoom: '聊天室',
  ChatDetail: '私信详情',
  Messages: '私信',
  Events: '活动',
  Dashboard: '数据面板',
  Friends: '好友',
  Learning: '在线学习',
  CourseDetail: '课程详情',
  MyLearning: '我的学习',
  Search: '搜索',
  Content: '内容中心',
  ContentCreate: '创建内容',
  ContentDetail: '内容详情',
  Activity: '校园动态',
}

const crumbs = computed<Crumb[]>(() => {
  const matched = route.matched
  const result: Crumb[] = [{ label: '首页', to: '/' }]

  matched.forEach(m => {
    const name = String(m.name || '')
    if (!name || name === 'Home') return
    const label = titleMap[name] || name
    const to = m.path.includes(':') ? undefined : m.path
    result.push({ label, to })
  })

  return result
})

const navigate = (crumb: Crumb, index: number) => {
  if (!crumb.to || index === crumbs.value.length - 1) return
  router.push(crumb.to)
}
</script>

<template>
  <nav v-if="crumbs.length > 1" class="breadcrumb" aria-label="面包屑导航">
    <ol class="breadcrumb-list">
      <li
        v-for="(crumb, index) in crumbs"
        :key="index"
        class="breadcrumb-item"
        :class="{ 'is-last': index === crumbs.length - 1 }"
      >
        <button
          v-if="crumb.to && index < crumbs.length - 1"
          type="button"
          class="breadcrumb-link"
          @click="navigate(crumb, index)"
        >
          {{ crumb.label }}
        </button>
        <span v-else class="breadcrumb-current">{{ crumb.label }}</span>
        <span v-if="index < crumbs.length - 1" class="breadcrumb-separator">
          <span class="i-ep-arrow-right" />
        </span>
      </li>
    </ol>
  </nav>
</template>

<style scoped>
.breadcrumb {
  padding: var(--space-4) 0;
}

.breadcrumb-list {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  list-style: none;
  gap: var(--space-2);
}

.breadcrumb-item {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 0.875rem;
}

.breadcrumb-link {
  color: var(--text-secondary);
  transition: color 0.2s;
}

.breadcrumb-link:hover {
  color: var(--primary-600);
}

.dark .breadcrumb-link:hover {
  color: var(--primary-400);
}

.breadcrumb-current {
  color: var(--text-primary);
  font-weight: 500;
}

.breadcrumb-separator {
  display: inline-flex;
  align-items: center;
  color: var(--text-tertiary);
}

.breadcrumb-separator span {
  width: 14px;
  height: 14px;
}
</style>
