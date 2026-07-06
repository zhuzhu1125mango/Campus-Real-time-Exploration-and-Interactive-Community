<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '../stores/userStore'

const userStore = useUserStore()
const isLoggedIn = computed(() => userStore.isLoggedIn)

const exploreLinks = [
  { label: '校园探索', to: '/explore' },
  { label: '院校查询', to: '/schools' },
  { label: '在线学习', to: '/learning' },
]

const communityLinks = [
  { label: '论坛', to: '/forum' },
  { label: '内容中心', to: '/content' },
  { label: '活动', to: '/events' },
]

const userLinks = [
  { label: '个人中心', to: '/profile' },
  { label: '我的收藏', to: '/my-favorite-schools' },
  { label: '我的学习', to: '/my-learning' },
]

const guestLinks = [
  { label: '登录', to: '/login' },
  { label: '注册', to: '/register' },
]
</script>

<template>
  <footer class="app-footer">
    <div class="container-wide footer-inner">
      <div class="footer-brand">
        <div class="footer-brand-title">
          <span class="brand-dot" />
          校园实时互动社区
        </div>
        <p class="footer-brand-desc">
          连接校园每一个角落，发现身边的精彩。
        </p>
      </div>

      <div class="footer-links">
        <div class="footer-column">
          <h4>探索</h4>
          <router-link
            v-for="link in exploreLinks"
            :key="link.to"
            :to="link.to"
            class="footer-link"
          >
            {{ link.label }}
          </router-link>
        </div>

        <div class="footer-column">
          <h4>社区</h4>
          <router-link
            v-for="link in communityLinks"
            :key="link.to"
            :to="link.to"
            class="footer-link"
          >
            {{ link.label }}
          </router-link>
        </div>

        <div class="footer-column">
          <h4>我的</h4>
          <router-link
            v-for="link in isLoggedIn ? userLinks : guestLinks"
            :key="link.to"
            :to="link.to"
            class="footer-link"
          >
            {{ link.label }}
          </router-link>
        </div>
      </div>
    </div>

    <div class="footer-bottom">
      <div class="container-wide footer-bottom-inner">
        <p>&copy; 2025 校园实时互动社区. All rights reserved.</p>
        <div class="footer-bottom-links">
          <router-link to="/search" class="footer-bottom-link">搜索</router-link>
          <router-link to="/dashboard" class="footer-bottom-link">数据面板</router-link>
        </div>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  background-color: var(--bg-primary);
  border-top: 1px solid var(--border-color-light);
  color: var(--text-secondary);
}

.footer-inner {
  display: grid;
  grid-template-columns: 1.2fr 2fr;
  gap: var(--space-8);
  padding-top: var(--space-10);
  padding-bottom: var(--space-10);
}

.footer-brand-title {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--space-3);
}

.brand-dot {
  width: 10px;
  height: 10px;
  border-radius: var(--radius-full);
  background: var(--primary-600);
  box-shadow: 0 0 0 4px var(--primary-100);
}

.dark .brand-dot {
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.25);
}

.footer-brand-desc {
  max-width: 280px;
  line-height: 1.6;
  font-size: 0.95rem;
}

.footer-links {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-6);
}

.footer-column h4 {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-4);
}

.footer-link {
  display: block;
  padding: var(--space-1) 0;
  font-size: 0.9rem;
  color: var(--text-secondary);
  transition: color 0.2s;
}

.footer-link:hover {
  color: var(--primary-600);
}

.dark .footer-link:hover {
  color: var(--primary-400);
}

.footer-bottom {
  border-top: 1px solid var(--border-color-light);
  padding: var(--space-4) 0;
}

.footer-bottom-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  font-size: 0.85rem;
}

.footer-bottom-links {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.footer-bottom-link {
  color: var(--text-tertiary);
  transition: color 0.2s;
}

.footer-bottom-link:hover {
  color: var(--primary-600);
}

.dark .footer-bottom-link:hover {
  color: var(--primary-400);
}

@media (max-width: 768px) {
  .footer-inner {
    grid-template-columns: 1fr;
    gap: var(--space-8);
  }

  .footer-links {
    grid-template-columns: repeat(2, 1fr);
  }

  .footer-bottom-inner {
    flex-direction: column;
    text-align: center;
  }
}
</style>
