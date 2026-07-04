<template>
  <div class="tag-detail-container">
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="6" animated />
      <p>加载中...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <el-alert :title="error" type="error" show-icon @close="error = null" />
      <div class="actions">
        <router-link to="/forum">
          <el-button type="primary">返回论坛</el-button>
        </router-link>
      </div>
    </div>

    <template v-else>
      <div class="tag-header">
        <div class="tag-info">
          <h1 class="tag-name">#{{ tag?.name }}</h1>
          <p class="tag-meta">共 {{ tag?.topic_count || 0 }} 个主题</p>
        </div>
        <router-link to="/forum">
          <el-button>返回论坛</el-button>
        </router-link>
      </div>

      <div class="topics-section">
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
              <span><i class="el-icon-view"></i> {{ topic.views || 0 }}</span>
              <span><i class="el-icon-chat-dot-square"></i> {{ topic.reply_count || 0 }}</span>
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
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { forumApi } from '@/api/forum'
import type { Topic } from '@/types/forum'

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
  } catch (err: any) {
    console.error('加载标签详情失败:', err)
    error.value = err?.response?.data?.detail || '加载标签详情失败'
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
.tag-detail-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.loading-state,
.error-state,
.empty-state {
  padding: 3rem 0;
  text-align: center;
}

.error-state .actions {
  margin-top: 1.5rem;
}

.tag-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.tag-name {
  margin: 0 0 0.5rem;
  font-size: 1.8rem;
  color: #4361ee;
}

.tag-meta {
  margin: 0;
  color: #6b7280;
}

.topics-section {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.section-title {
  margin: 0 0 1.5rem;
  font-size: 1.3rem;
  color: #1f2937;
}

.topic-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.topic-card {
  padding: 1.2rem;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.topic-card:hover {
  border-color: #4361ee;
  box-shadow: 0 4px 12px rgba(67, 97, 238, 0.1);
}

.topic-title {
  margin: 0 0 0.6rem;
  font-size: 1.1rem;
  color: #1f2937;
}

.topic-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: #6b7280;
}

.topic-author {
  color: #4361ee;
  font-weight: 500;
}

.topic-stats {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: #6b7280;
}

.pagination {
  margin-top: 2rem;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .tag-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }

  .topic-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.8rem;
  }

  .topic-stats {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
