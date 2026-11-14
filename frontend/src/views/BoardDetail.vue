<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { forumApi } from '../api/forum'
import type { Board, Topic } from '../types/forum'
import { useUserStore } from '../stores/userStore'
import RichTextEditor from '../components/RichTextEditor.vue'
import GlassCard from '../components/GlassCard.vue'
import SectionHeader from '../components/SectionHeader.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 状态
const board = ref<Board>({} as Board)
const topics = ref<Topic[]>([])
const loading = ref(true)
const submitting = ref(false)
const showNewTopicForm = ref(false)
const filter = ref('latest')
const searchQuery = ref('')
const currentPage = ref(1)
const totalTopics = ref(0)

// 新主题表单
const newTopic = reactive({
  title: '',
  content: '',
  tags: [] as string[]
})

// 标签输入
const tagInput = ref('')

// 计算属性
const isLoggedIn = computed(() => {
  return userStore.isLoggedIn
})

const totalPages = computed(() => {
  return Math.ceil(totalTopics.value / 10)
})

// 获取版块信息
const fetchBoard = async () => {
  try {
    const boardId = Number(route.params.boardId)
    if (!boardId) return

    const response = await forumApi.getBoard(boardId)
    board.value = response
  } catch (error) {
    console.error('获取版块信息失败:', error)
  }
}

// 获取主题列表
const fetchTopics = async () => {
  loading.value = true
  try {
    const boardId = Number(route.params.boardId)
    if (!boardId) return

    const response = await forumApi.getTopics(boardId, currentPage.value)
    topics.value = response.results
    totalTopics.value = response.count
  } catch (error) {
    console.error('获取主题列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 添加标签
const addTag = () => {
  const tag = tagInput.value.trim()
  if (tag && !newTopic.tags.includes(tag)) {
    newTopic.tags.push(tag)
  }
  tagInput.value = ''
}

// 逗号键也触发添加标签
const handleTagComma = (event: KeyboardEvent) => {
  if (event.key === ',') {
    event.preventDefault()
    addTag()
  }
}

// 移除标签
const removeTag = (index: number) => {
  newTopic.tags.splice(index, 1)
}

// 提交新主题
const submitTopic = async () => {
  if (!board.value.id) return

  submitting.value = true
  try {
    await forumApi.createTopic(board.value.id, {
      title: newTopic.title,
      content: newTopic.content,
      tags: newTopic.tags
    })

    // 重置表单
    newTopic.title = ''
    newTopic.content = ''
    newTopic.tags = []
    showNewTopicForm.value = false

    // 刷新主题列表
    currentPage.value = 1
    await fetchTopics()
  } catch (error) {
    console.error('发布主题失败:', error)
    alert('发布主题失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

// 设置筛选条件
const setFilter = (newFilter: string) => {
  filter.value = newFilter
  currentPage.value = 1
  fetchTopics()
}

// 搜索主题
const searchTopics = () => {
  currentPage.value = 1
  fetchTopics()
}

// 分页
const changePage = (page: number) => {
  currentPage.value = page
  fetchTopics()
}

// 跳转到主题详情
const goToTopicDetail = (topicId: number) => {
  router.push(`/forum/topic/${topicId}`)
}

// 获取主题状态类
const getTopicStatusClass = (topic: Topic) => {
  if (topic.status === 'pinned') return 'status-pinned'
  if (topic.status === 'closed') return 'status-closed'
  return 'status-normal'
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '未知'

  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // 小于一天，显示相对时间
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000))
    if (hours === 0) {
      const minutes = Math.floor(diff / (60 * 1000))
      return minutes <= 0 ? '刚刚' : `${minutes}分钟前`
    }
    return `${hours}小时前`
  }

  // 显示年月日
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

// 生命周期钩子
onMounted(async () => {
  await fetchBoard()
  await fetchTopics()
})
</script>

<template>
  <div class="board-detail-page container-wide page-padding">
    <div v-if="loading && topics.length === 0" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <template v-else>
      <!-- 版块信息 -->
      <SectionHeader
        :title="board.name || '版块详情'"
        :subtitle="board.description || ''"
        icon="i-ep-grid"
        :action="isLoggedIn ? { label: '发布新主题', onClick: () => showNewTopicForm = true } : undefined"
      />

      <!-- 新主题表单弹窗 -->
      <div v-if="showNewTopicForm" class="modal-overlay" @click.self="showNewTopicForm = false">
        <GlassCard :hover="false" class="new-topic-modal">
          <h2 class="form-title">发布新主题</h2>
          <form @submit.prevent="submitTopic">
            <div class="form-group">
              <label for="topic-title">标题</label>
              <input
                id="topic-title"
                v-model="newTopic.title"
                type="text"
                required
                placeholder="请输入主题标题"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="topic-content">内容</label>
              <RichTextEditor
                v-model="newTopic.content"
                placeholder="请输入主题内容"
              />
            </div>
            <div class="form-group">
              <label for="topic-tags">标签</label>
              <div class="tags-input-container">
                <div v-for="(tag, index) in newTopic.tags" :key="index" class="tag-item">
                  {{ tag }}
                  <span class="tag-remove" @click="removeTag(index)">×</span>
                </div>
                <input
                  id="topic-tags"
                  v-model="tagInput"
                  class="tag-input"
                  placeholder="输入标签后按Enter添加"
                  @keydown.enter.prevent="addTag"
                  @keydown.tab.prevent="addTag"
                  @keydown="handleTagComma"
                />
              </div>
              <div class="tags-helper">用标签归类你的主题，多个标签用回车分隔</div>
            </div>
            <div class="form-actions">
              <button type="button" class="btn btn-secondary" @click="showNewTopicForm = false">
                取消
              </button>
              <button type="submit" class="btn btn-primary" :disabled="submitting">
                <span v-if="submitting" class="loading-spinner small"></span>
                <span>{{ submitting ? '发布中...' : '发布' }}</span>
              </button>
            </div>
          </form>
        </GlassCard>
      </div>

      <!-- 主题列表 -->
      <GlassCard :hover="false" class="topics-card">
        <div class="topics-header">
          <div class="topics-filter">
            <button
              class="filter-btn"
              :class="{ active: filter === 'latest' }"
              @click="setFilter('latest')"
            >
              最新
            </button>
            <button
              class="filter-btn"
              :class="{ active: filter === 'hot' }"
              @click="setFilter('hot')"
            >
              热门
            </button>
          </div>
          <div class="topics-search">
            <span class="i-ep-search search-icon" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索主题..."
              @keyup.enter="searchTopics"
            />
            <button class="search-btn" @click="searchTopics">
              <span class="i-ep-search" />
            </button>
          </div>
        </div>

        <div v-if="topics.length > 0" class="topics-list">
          <div
            v-for="topic in topics"
            :key="topic.id"
            class="topic-row"
            @click="goToTopicDetail(topic.id)"
          >
            <div class="topic-main">
              <div class="topic-title-line">
                <div class="topic-status" :class="getTopicStatusClass(topic)"></div>
                <h3 class="topic-title">{{ topic.title }}</h3>
              </div>
              <div class="topic-meta">
                <span class="topic-date">发布于 {{ formatDate(topic.created_at) }}</span>
                <div v-if="topic.tags && topic.tags.length > 0" class="topic-tags">
                  <span v-for="tag in topic.tags" :key="tag.id" class="topic-tag">
                    {{ tag.name }}
                  </span>
                </div>
              </div>
            </div>
            <div class="topic-author">
              <img v-if="topic.author.avatar" :src="topic.author.avatar" alt="avatar" class="author-avatar" />
              <div v-else class="author-avatar-placeholder">{{ topic.author.username.substring(0, 1) }}</div>
              <span class="author-name">{{ topic.author.username }}</span>
            </div>
            <div class="topic-stats">
              <span class="stat-item">
                <span class="i-ep-view stat-icon" />
                {{ topic.views }}
              </span>
              <span class="stat-item">
                <span class="i-ep-chat-dot-round stat-icon" />
                {{ topic.post_count - 1 }}
              </span>
            </div>
            <div class="topic-last-post">
              {{ formatDate(topic.updated_at) }}
            </div>
          </div>
        </div>

        <div v-else class="empty-topics">
          <span class="i-ep-document empty-icon" />
          <p>暂无主题，来发布第一个主题吧！</p>
        </div>

        <!-- 分页 -->
        <div v-if="totalPages > 1" class="pagination">
          <button
            class="btn btn-secondary"
            :disabled="currentPage === 1"
            @click="changePage(currentPage - 1)"
          >
            上一页
          </button>
          <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
          <button
            class="btn btn-secondary"
            :disabled="currentPage === totalPages"
            @click="changePage(currentPage + 1)"
          >
            下一页
          </button>
        </div>
      </GlassCard>
    </template>
  </div>
</template>

<style scoped>
.board-detail-page {
  color: var(--text-primary);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5rem 0;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--primary-200);
  border-top-color: var(--primary-600);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.loading-spinner.small {
  width: 16px;
  height: 16px;
  border-width: 2px;
  margin: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 新主题表单弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 1rem;
}

.new-topic-modal {
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
}

.form-title {
  margin: 0 0 1.5rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: var(--text-primary);
}

.form-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 1rem;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-500);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
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

/* 主题列表 */
.topics-card {
  overflow: hidden;
}

.topics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 1rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid var(--border-color-light);
  gap: 1rem;
}

.topics-filter {
  display: flex;
  gap: 0.5rem;
}

.filter-btn {
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn:hover {
  border-color: var(--primary-400);
  color: var(--primary-600);
}

.filter-btn.active {
  background-color: var(--primary-600);
  border-color: var(--primary-600);
  color: white;
}

.topics-search {
  display: flex;
  align-items: center;
  max-width: 280px;
}

.topics-search .search-icon {
  margin-right: 0.5rem;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.topics-search input {
  flex: 1;
  min-width: 0;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md) 0 0 var(--radius-md);
  border-right: none;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.topics-search input:focus {
  outline: none;
  border-color: var(--primary-500);
}

.search-btn {
  padding: 0.5rem 0.875rem;
  background: var(--primary-600);
  color: white;
  border: none;
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  cursor: pointer;
  transition: background 0.2s;
}

.search-btn:hover {
  background: var(--primary-700);
}

.topics-list {
  display: flex;
  flex-direction: column;
}

.topic-row {
  display: grid;
  grid-template-columns: 3fr 1fr 1fr 1fr;
  align-items: center;
  gap: 1rem;
  padding: 1rem 0;
  border-bottom: 1px solid var(--border-color-light);
  cursor: pointer;
  transition: background 0.2s;
}

.topic-row:hover {
  background: var(--bg-tertiary);
  margin: 0 -1.25rem;
  padding-left: 1.25rem;
  padding-right: 1.25rem;
}

.topic-main {
  min-width: 0;
}

.topic-title-line {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.topic-status {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-normal {
  background-color: var(--success-color);
}

.status-pinned {
  background-color: var(--error-color);
}

.status-closed {
  background-color: var(--text-tertiary);
}

.topic-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.topic-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.topic-date {
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.topic-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.topic-tag {
  background-color: var(--primary-50);
  color: var(--primary-700);
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: var(--radius-full);
}

.topic-author {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
}

.author-avatar,
.author-avatar-placeholder {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.author-avatar-placeholder {
  background: linear-gradient(135deg, var(--primary-500), var(--primary-700));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.75rem;
}

.author-name {
  color: var(--text-secondary);
  font-size: 0.875rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.topic-stats {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.stat-icon {
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.topic-last-post {
  color: var(--text-secondary);
  font-size: 0.875rem;
  text-align: right;
}

.empty-topics {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 3rem 0;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.4;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  padding-top: 1.5rem;
  margin-top: 1rem;
  border-top: 1px solid var(--border-color-light);
  gap: 1rem;
}

.page-info {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

/* 标签相关样式 */
.tags-input-container {
  display: flex;
  flex-wrap: wrap;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 0.5rem;
  gap: 0.5rem;
  min-height: 46px;
  background: var(--bg-primary);
}

.tag-item {
  display: flex;
  align-items: center;
  background-color: var(--primary-50);
  color: var(--primary-700);
  border-radius: var(--radius-full);
  padding: 0.25rem 0.625rem;
  font-size: 0.875rem;
}

.tag-remove {
  margin-left: 0.375rem;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
}

.tag-input {
  border: none;
  outline: none;
  flex: 1;
  min-width: 100px;
  padding: 0.25rem;
  font-size: 0.875rem;
  background: transparent;
  color: var(--text-primary);
}

.tags-helper {
  margin-top: 0.375rem;
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

@media (max-width: 768px) {
  .topics-header {
    flex-direction: column;
    align-items: stretch;
  }

  .topics-search {
    max-width: none;
  }

  .topic-row {
    grid-template-columns: 1fr auto;
    gap: 0.75rem 0.5rem;
  }

  .topic-main {
    grid-column: 1 / -1;
  }

  .topic-author {
    grid-column: 1;
  }

  .topic-stats {
    grid-column: 2;
    flex-direction: row;
    justify-content: flex-end;
  }

  .topic-last-post {
    display: none;
  }
}
</style>
