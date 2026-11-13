<template>
  <div class="tag-detail-page container-wide page-padding">
    <SectionHeader
      title="标签详情"
      subtitle="浏览标签下的相关主题"
      icon="i-ep-collection-tag"
    />

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="6" animated />
      <p>加载中...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <el-alert :title="error" type="error" show-icon @close="error = null" />
      <div class="error-actions">
        <router-link to="/forum">
          <button class="btn btn-primary">
            <span class="i-ep-back" />
            返回论坛
          </button>
        </router-link>
      </div>
    </div>

    <template v-else>
      <GlassCard :hover="false" class="tag-header-card">
        <div class="tag-header">
          <div class="tag-info">
            <h1 class="tag-name">#{{ tag?.name }}</h1>
            <p class="tag-meta">共 {{ tag?.topic_count || 0 }} 个主题</p>
          </div>
          <router-link to="/forum">
            <button class="btn btn-secondary">
              <span class="i-ep-back" />
              返回论坛
            </button>
          </router-link>
        </div>
      </GlassCard>

      <GlassCard :hover="false" class="topics-card">
        <h2 class="section-title">相关主题</h2>

        <div v-if="topicsLoading" class="loading-state">
          <el-skeleton :rows="4" animated />
        </div>

        <div v-else-if="topics.length === 0" class="empty-state">
          <el-empty description="该标签下还没有主题" />
        </div>

        <div v-else class="topic-list">
          <div
            v-for="topic in topics"
            :key="topic.id"
            class="topic-card"
            @click="goToTopic(topic.id)"
          >
            <div class="topic-main">
              <h3 class="topic-title">{{ topic.title }}</h3>
              <div class="topic-meta">
                <span class="topic-author">{{ topic.author?.username || '匿名用户' }}</span>
                <span class="topic-time">{{ formatTime(topic.created_at) }}</span>
              </div>
            </div>
            <div class="topic-stats">
              <span><span class="i-ep-view" /> {{ topic.views || 0 }}</span>
              <span><span class="i-ep-chat-dot-round" /> {{ topic.reply_count || 0 }}</span>
            </div>
          </div>
        </div>

        <div v-if="totalPages > 1" class="pagination">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next"
            @current-change="handlePageChange"
          />
        </div>
      </GlassCard>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { forumApi } from '@/api/forum'
import { getApiErrorMessage } from '@/utils/error'
import type { Topic } from '@/types/forum'
import GlassCard from '@/components/GlassCard.vue'
import SectionHeader from '@/components/SectionHeader.vue'

const route = useRoute()
const router = useRouter()

const tagId = computed(() => Number(route.params.tagId))
const tag = ref<{ id: number; name: string; topic_count: number } | null>(null)
const topics = ref<Topic[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const loading = ref(true)
const topicsLoading = ref(false)
const error = ref<string | null>(null)

const fetchTagData = async () => {
  if (isNaN(tagId.value) || tagId.value <= 0) {
    error.value = '无效的标签ID'
    loading.value = false
    return
  }

  loading.value = true
  error.value = null

  try {
    const [tagRes] = await Promise.all([
      forumApi.getTag(tagId.value),
      fetchTopics()
    ])
    tag.value = tagRes
  } catch (err) {
    console.error('加载标签详情失败:', err)
    error.value = getApiErrorMessage(err, '加载标签详情失败')
  } finally {
    loading.value = false
  }
}

const fetchTopics = async () => {
  if (isNaN(tagId.value) || tagId.value <= 0) return

  topicsLoading.value = true
  try {
    const response = await forumApi.getTagTopics(tagId.value, currentPage.value, pageSize.value)
    topics.value = response.results || []
    total.value = response.count || 0
  } catch (err) {
    console.error('获取标签主题失败:', err)
    topics.value = []
    total.value = 0
  } finally {
    topicsLoading.value = false
  }
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchTopics()
}

const goToTopic = (topicId: number) => {
  router.push(`/forum/topic/${topicId}`)
}

const formatTime = (timeString: string) => {
  if (!timeString) return ''
  const date = new Date(timeString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  fetchTagData()
})

watch(tagId, () => {
  currentPage.value = 1
  fetchTagData()
})
</script>

<style scoped>
.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-10) 0;
  color: var(--text-secondary);
}

.error-actions {
  margin-top: var(--space-5);
}

.tag-header-card {
  margin-bottom: var(--space-5);
}

.tag-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tag-name {
  margin: 0 0 var(--space-2);
  font-size: 1.8rem;
  color: var(--primary-600);
}

.tag-meta {
  margin: 0;
  color: var(--text-secondary);
}

.section-title {
  margin: 0 0 var(--space-5);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.topic-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.topic-card {
  padding: var(--space-4);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-primary);
}

.topic-card:hover {
  border-color: var(--primary-600);
  box-shadow: var(--shadow-md);
}

.topic-title {
  margin: 0 0 var(--space-2);
  font-size: 1.1rem;
  color: var(--text-primary);
}

.topic-meta {
  display: flex;
  gap: var(--space-4);
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.topic-author {
  color: var(--primary-600);
  font-weight: 500;
}

.topic-stats {
  display: flex;
  gap: var(--space-4);
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.topic-stats span {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

.pagination {
  margin-top: var(--space-6);
  display: flex;
  justify-content: center;
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

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .tag-header {
    flex-direction: column;
    gap: var(--space-4);
    align-items: flex-start;
  }

  .topic-card {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-3);
  }

  .topic-stats {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
