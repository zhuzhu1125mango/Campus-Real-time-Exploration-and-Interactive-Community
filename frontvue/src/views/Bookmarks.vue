<template>
  <div class="bookmarks-container">
    <h1 class="page-title">我的收藏</h1>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="bookmarks.length === 0" class="empty-bookmarks">
      <div class="empty-icon"></div>
      <p>您还没有收藏任何主题</p>
      <router-link to="/forum" class="btn-to-forum">浏览论坛</router-link>
    </div>

    <div v-else class="bookmarks-list">
      <div v-for="topic in bookmarks" :key="topic.id" class="bookmark-item" @click="goToTopicDetail(topic.id)">
        <div class="topic-info">
          <h3 class="topic-title">{{ topic.title }}</h3>
          <div class="topic-meta">
            <span class="board-name">{{ getBoardName(topic.board) }}</span>
            <span class="topic-status" :class="getTopicStatusClass(topic)">
              {{ getTopicStatusText(topic) }}
            </span>
            <span class="topic-date">{{ formatDate(topic.created_at) }}</span>
          </div>
        </div>
        <div class="topic-stats">
          <div class="stat-item">
            <span class="icon-view"></span>
            <span>{{ topic.views }}</span>
          </div>
          <div class="stat-item">
            <span class="icon-reply"></span>
            <span>{{ topic.posts_count - 1 }}</span>
          </div>
        </div>
        <button class="btn-remove" @click.stop="removeBookmark(topic.id)">
          <span class="icon-remove"></span>
        </button>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="pagination">
        <button 
          class="btn-page" 
          :disabled="currentPage === 1" 
          @click="changePage(currentPage - 1)"
        >
          上一页
        </button>
        <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
        <button 
          class="btn-page" 
          :disabled="currentPage === totalPages" 
          @click="changePage(currentPage + 1)"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { forumApi } from '../api/forum'
import type { Topic, Board } from '../types/forum'

const router = useRouter()

// 状态
const bookmarks = ref<Topic[]>([])
const boards = ref<Board[]>([])
const loading = ref(true)
const currentPage = ref(1)
const totalBookmarks = ref(0)

// 计算属性
const totalPages = computed(() => {
  return Math.ceil(totalBookmarks.value / 10)
})

// 获取收藏主题列表
const fetchBookmarks = async () => {
  loading.value = true
  try {
    const response = await forumApi.getBookmarks(currentPage.value)
    bookmarks.value = response.results
    totalBookmarks.value = response.count
  } catch (error) {
    console.error('获取收藏失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取所有版块列表（用于显示版块名称）
const fetchBoards = async () => {
  try {
    const response = await forumApi.getBoards()
    boards.value = response.results
  } catch (error) {
    console.error('获取版块列表失败:', error)
  }
}

// 根据版块ID获取版块名称
const getBoardName = (boardId: number) => {
  const board = boards.value.find(b => b.id === boardId)
  return board ? board.name : '未知版块'
}

// 移除收藏
const removeBookmark = async (topicId: number) => {
  try {
    await forumApi.unbookmarkTopic(topicId)
    bookmarks.value = bookmarks.value.filter(t => t.id !== topicId)
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
const goToTopicDetail = (topicId: number) => {
  router.push(`/forum/topic/${topicId}`)
}

// 获取主题状态类
const getTopicStatusClass = (topic: Topic) => {
  if (topic.status === 'pinned') return 'status-pinned'
  if (topic.status === 'closed') return 'status-closed'
  return 'status-open'
}

// 获取主题状态文本
const getTopicStatusText = (topic: Topic) => {
  if (topic.status === 'pinned') return '置顶'
  if (topic.status === 'closed') return '已关闭'
  if (topic.status === 'archived') return '已归档'
  return '进行中'
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '未知'
  
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

// 生命周期钩子
onMounted(async () => {
  await Promise.all([fetchBookmarks(), fetchBoards()])
})
</script>

<style scoped>
.bookmarks-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.page-title {
  font-size: 24px;
  margin-bottom: 30px;
  color: #333;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 50px 0;
}

.loading-spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top: 4px solid #3498db;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-bookmarks {
  text-align: center;
  padding: 50px 0;
  color: #666;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 20px;
  opacity: 0.3;
}

.empty-icon::before {
  content: "🔖";
}

.btn-to-forum {
  display: inline-block;
  margin-top: 20px;
  padding: 10px 20px;
  background-color: #3498db;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-weight: 500;
}

.bookmarks-list {
  margin-bottom: 30px;
}

.bookmark-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 20px;
  background-color: white;
  border-radius: 8px;
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: transform 0.2s;
}

.bookmark-item:hover {
  transform: translateY(-3px);
}

.topic-info {
  flex: 1;
}

.topic-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #333;
}

.topic-meta {
  display: flex;
  gap: 15px;
  color: #666;
  font-size: 14px;
  align-items: center;
}

.topic-status {
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
}

.status-open {
  background-color: #2ecc71;
  color: white;
}

.status-pinned {
  background-color: #e74c3c;
  color: white;
}

.status-closed {
  background-color: #95a5a6;
  color: white;
}

.topic-stats {
  display: flex;
  gap: 15px;
  margin-right: 15px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #666;
  font-size: 14px;
}

.icon-view::before {
  content: "👁️";
}

.icon-reply::before {
  content: "💬";
}

.btn-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background-color: transparent;
  border: 1px solid #ddd;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-remove:hover {
  background-color: #f1f1f1;
  border-color: #e74c3c;
  color: #e74c3c;
}

.icon-remove::before {
  content: "×";
  font-size: 18px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 30px;
  gap: 20px;
}

.btn-page {
  padding: 8px 15px;
  background-color: #f1f1f1;
  border: none;
  border-radius: 4px;
  color: #333;
  cursor: pointer;
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #666;
}

@media (max-width: 768px) {
  .bookmark-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .topic-stats {
    margin-top: 10px;
    margin-right: 0;
  }
  
  .btn-remove {
    position: absolute;
    top: 15px;
    right: 15px;
  }
}
</style> 