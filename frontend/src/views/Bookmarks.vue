<template>
  <div class="bookmarks-page container-medium page-padding">
    <SectionHeader
      title="我的收藏"
      subtitle="查看和管理你感兴趣的主题收藏"
      icon="i-ep-star"
    />

    <GlassCard :hover="false" class="bookmarks-card">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner" />
        <p>加载中...</p>
      </div>

      <div v-else-if="validBookmarks.length === 0" class="empty-state">
        <div class="empty-icon">
          <span class="i-ep-star" />
        </div>
        <p>您还没有收藏任何主题</p>
        <router-link to="/forum" class="btn btn-primary">
          <span class="i-ep-document" />
          浏览论坛
        </router-link>
      </div>

      <div v-else class="bookmarks-list">
        <div
          v-for="bookmark in validBookmarks"
          :key="bookmark?.id"
          class="bookmark-item"
          @click="goToTopicDetail(bookmark?.topic)"
        >
          <div class="topic-info">
            <h3 class="topic-title">收藏主题 {{ bookmark?.topic }}</h3>
            <div class="topic-meta">
              <span class="topic-date">
                <span class="i-ep-calendar meta-icon" />
                {{ formatDate(bookmark?.created_at || '') }}
              </span>
            </div>
          </div>
          <button
            class="btn btn-danger btn-icon"
            title="移除收藏"
            @click.stop="removeBookmark(bookmark?.id)"
          >
            <span class="i-ep-delete" />
          </button>
        </div>

        <!-- 分页 -->
        <div v-if="totalPages > 1" class="pagination">
          <button
            class="btn btn-secondary"
            :disabled="currentPage === 1"
            @click="changePage(currentPage - 1)"
          >
            <span class="i-ep-arrow-left" />
            上一页
          </button>
          <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
          <button
            class="btn btn-secondary"
            :disabled="currentPage === totalPages"
            @click="changePage(currentPage + 1)"
          >
            下一页
            <span class="i-ep-arrow-right" />
          </button>
        </div>
      </div>
    </GlassCard>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { forumApi } from '../api/forum'
import type { Bookmark } from '../types/forum'
import GlassCard from '../components/GlassCard.vue'
import SectionHeader from '../components/SectionHeader.vue'

const router = useRouter()

// 状态
const bookmarks = ref<Bookmark[]>([])
const loading = ref(true)
const currentPage = ref(1)
const totalBookmarks = ref(0)

// 过滤掉后端可能返回的 null/undefined 项，避免渲染时读取 .id 报错
const validBookmarks = computed(() => bookmarks.value.filter(Boolean))

// 计算属性
const totalPages = computed(() => {
  return Math.ceil(totalBookmarks.value / 10)
})

// 获取收藏主题列表
const fetchBookmarks = async () => {
  loading.value = true
  try {
    const response = await forumApi.getBookmarks()
    bookmarks.value = response
    totalBookmarks.value = response.length
  } catch (error) {
    console.error('获取收藏失败:', error)
  } finally {
    loading.value = false
  }
}

// 移除收藏
const removeBookmark = async (topicId: number | undefined) => {
  if (!topicId) return
  try {
    await forumApi.unbookmarkTopic(topicId)
    bookmarks.value = bookmarks.value.filter(t => t?.id !== topicId)
    totalBookmarks.value--
  } catch (error) {
    console.error('移除收藏失败:', error)
  }
}

// 分页
const changePage = (page: number) => {
  currentPage.value = page
  fetchBookmarks()
}

// 跳转到主题详情
const goToTopicDetail = (topicId: number | undefined) => {
  if (!topicId) return
  router.push(`/forum/topic/${topicId}`)
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '未知'

  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

// 生命周期钩子
onMounted(async () => {
  await fetchBookmarks()
})
</script>

<style scoped>
.bookmarks-page {
  min-height: calc(100vh - 200px);
}

.bookmarks-card {
  min-height: 400px;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-10) 0;
  color: var(--text-secondary);
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(67, 97, 238, 0.2);
  border-radius: 50%;
  border-top-color: var(--primary-500);
  animation: spin 1s linear infinite;
  margin-bottom: var(--space-3);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--primary-50);
  color: var(--primary-500);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-4);
  font-size: 2rem;
}

.bookmarks-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.bookmark-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.25s ease;
  gap: var(--space-4);
}

.bookmark-item:hover {
  border-color: var(--primary-600);
  box-shadow: var(--shadow-md);
}

.topic-info {
  flex: 1;
  min-width: 0;
}

.topic-title {
  margin: 0 0 var(--space-2);
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-primary);
}

.topic-meta {
  display: flex;
  gap: var(--space-3);
  color: var(--text-tertiary);
  font-size: 0.875rem;
  align-items: center;
}

.topic-date {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

.meta-icon {
  font-size: 1rem;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: var(--space-6);
  gap: var(--space-4);
}

.page-info {
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 500;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
  text-decoration: none;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: var(--primary-600);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--primary-700);
}

.btn-secondary {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-secondary:hover:not(:disabled) {
  background-color: var(--border-color);
}

.btn-danger {
  background-color: var(--danger-50);
  color: var(--danger-600);
}

.btn-danger:hover:not(:disabled) {
  background-color: var(--danger-100);
}

.btn-icon {
  width: 40px;
  height: 40px;
  padding: 0;
  border-radius: 50%;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .bookmark-item {
    align-items: flex-start;
  }

  .btn-icon {
    width: 36px;
    height: 36px;
  }
}
</style>
