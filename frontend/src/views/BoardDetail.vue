<template>
  <div class="board-detail-container">
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner large"></div>
      <p>加载中...</p>
    </div>
    
    <template v-else>
      <!-- 版块信息 -->
      <div class="board-header">
        <div class="board-info">
          <h1 class="board-title">{{ board.name }}</h1>
          <p class="board-description">{{ board.description }}</p>
        </div>
        <div class="board-actions" v-if="isLoggedIn">
          <button class="btn-new-topic" @click="showNewTopicForm = true">
            <span class="icon-plus"></span>
            发布新主题
          </button>
        </div>
      </div>

      <!-- 新主题表单 -->
      <div v-if="showNewTopicForm" class="new-topic-form-container">
        <div class="new-topic-form">
          <h2>发布新主题</h2>
          <form @submit.prevent="submitTopic">
            <div class="form-group">
              <label for="topic-title">标题</label>
              <input
                id="topic-title"
                v-model="newTopic.title"
                type="text"
                required
                placeholder="请输入主题标题"
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
                  @keydown.enter.prevent="addTag"
                  @keydown.tab.prevent="addTag"
                  @keydown.comma.prevent="addTag"
                  placeholder="输入标签后按Enter添加"
                  class="tag-input"
                />
              </div>
              <div class="tags-helper">用标签归类你的主题，多个标签用回车分隔</div>
            </div>
            <div class="form-actions">
              <button type="button" class="btn-cancel" @click="showNewTopicForm = false">取消</button>
              <button type="submit" class="btn-submit" :disabled="submitting">
                <span v-if="submitting" class="loading-spinner"></span>
                <span>{{ submitting ? '发布中...' : '发布' }}</span>
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- 主题列表 -->
      <div class="topics-container">
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
            <input 
              type="text" 
              v-model="searchQuery" 
              placeholder="搜索主题..." 
              @keyup.enter="searchTopics"
            />
            <button class="search-btn" @click="searchTopics">搜索</button>
          </div>
        </div>
        
        <table class="topics-table" v-if="topics.length > 0">
          <thead>
            <tr>
              <th class="topic-title-col">主题</th>
              <th class="topic-author-col">作者</th>
              <th class="topic-stats-col">统计</th>
              <th class="topic-last-post-col">最后回复</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="topic in topics" :key="topic.id" class="topic-row" @click="goToTopicDetail(topic.id)">
              <td class="topic-title-cell">
                <div class="topic-status" :class="getTopicStatusClass(topic)"></div>
                <div class="topic-info">
                  <h3 class="topic-title">{{ topic.title }}</h3>
                  <div class="topic-meta">
                    <span class="topic-date">发布于 {{ formatDate(topic.created_at) }}</span>
                    <div v-if="topic.tags && topic.tags.length > 0" class="topic-tags">
                      <span v-for="tag in topic.tags" :key="tag.id" class="topic-tag">
                        {{ tag.name }}
                      </span>
                    </div>
                  </div>
                </div>
              </td>
              <td class="topic-author-cell">
                <div class="author-info">
                  <img v-if="topic.author.avatar" :src="topic.author.avatar" alt="avatar" class="author-avatar" />
                  <div v-else class="author-avatar-placeholder">{{ topic.author.username.substring(0, 1) }}</div>
                  <span class="author-name">{{ topic.author.username }}</span>
                </div>
              </td>
              <td class="topic-stats-cell">
                <div class="topic-stats">
                  <div class="stat-item">
                    <span class="icon-view"></span>
                    <span>{{ topic.views }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="icon-reply"></span>
                    <span>{{ topic.post_count - 1 }}</span>
                  </div>
                </div>
              </td>
              <td class="topic-last-post-cell">
                <div class="last-post-time">{{ formatDate(topic.updated_at) }}</div>
              </td>
            </tr>
          </tbody>
        </table>
        
        <div v-else class="empty-topics">
          <div class="empty-icon"></div>
          <p>暂无主题，来发布第一个主题吧！</p>
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
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { forumApi } from '../api/forum'
import type { Board, Topic } from '../types/forum'
import config from '../utils/config'
import RichTextEditor from '../components/RichTextEditor.vue'

const route = useRoute()
const router = useRouter()

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
  return !!localStorage.getItem(config.jwt.accessTokenKey)
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

<style scoped>
.board-detail-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
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

.board-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.board-title {
  font-size: 28px;
  margin: 0 0 8px 0;
  color: #333;
}

.board-description {
  margin: 0;
  color: #666;
}

.board-actions {
  display: flex;
}

.btn-new-topic {
  display: flex;
  align-items: center;
  padding: 10px 20px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-new-topic:hover {
  background-color: #2980b9;
}

.icon-plus::before {
  content: "+";
  font-size: 18px;
  margin-right: 5px;
}

/* 新主题表单 */
.new-topic-form-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.new-topic-form {
  width: 90%;
  max-width: 800px;
  background-color: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.2);
}

.new-topic-form h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.form-group textarea {
  resize: vertical;
  min-height: 200px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-top: 30px;
}

.btn-cancel {
  padding: 10px 20px;
  background-color: #f1f1f1;
  border: none;
  border-radius: 4px;
  color: #333;
  font-weight: 500;
  cursor: pointer;
}

.btn-submit {
  padding: 10px 20px;
  background-color: #3498db;
  border: none;
  border-radius: 4px;
  color: white;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-submit:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

/* 主题列表 */
.topics-container {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.topics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #eee;
}

.topics-filter {
  display: flex;
  gap: 10px;
}

.filter-btn {
  padding: 6px 15px;
  background-color: transparent;
  border: 1px solid #ddd;
  border-radius: 4px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn.active {
  background-color: #3498db;
  border-color: #3498db;
  color: white;
}

.topics-search {
  display: flex;
}

.topics-search input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px 0 0 4px;
  width: 240px;
}

.search-btn {
  padding: 8px 15px;
  background-color: #3498db;
  border: none;
  border-radius: 0 4px 4px 0;
  color: white;
  cursor: pointer;
}

.topics-table {
  width: 100%;
  border-collapse: collapse;
}

.topics-table th {
  padding: 15px 20px;
  text-align: left;
  font-weight: 500;
  color: #666;
  background-color: #f8f9fa;
  border-bottom: 1px solid #eee;
}

.topic-row {
  cursor: pointer;
  transition: background-color 0.2s;
}

.topic-row:hover {
  background-color: #f9f9f9;
}

.topic-row td {
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
}

.topic-title-col {
  width: 50%;
}

.topic-author-col {
  width: 15%;
}

.topic-stats-col {
  width: 15%;
}

.topic-last-post-col {
  width: 20%;
}

.topic-title-cell {
  display: flex;
  align-items: center;
}

.topic-status {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 15px;
}

.status-normal {
  background-color: #2ecc71;
}

.status-pinned {
  background-color: #e74c3c;
}

.status-closed {
  background-color: #95a5a6;
}

.topic-info {
  flex: 1;
}

.topic-title {
  margin: 0 0 5px 0;
  font-size: 16px;
  color: #333;
}

.topic-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.topic-date {
  color: #999;
  font-size: 13px;
}

.topic-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.topic-tag {
  background-color: #e1f5fe;
  color: #0288d1;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
}

.author-info {
  display: flex;
  align-items: center;
}

.author-avatar, 
.author-avatar-placeholder {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  margin-right: 10px;
  overflow: hidden;
}

.author-avatar-placeholder {
  background-color: #3498db;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.topic-stats {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #666;
  font-size: 13px;
}

.icon-view::before {
  content: "👁️";
}

.icon-reply::before {
  content: "💬";
}

.last-post-time {
  font-size: 13px;
  color: #666;
}

.empty-topics {
  padding: 50px 20px;
  text-align: center;
  color: #666;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 20px;
  opacity: 0.3;
}

.empty-icon::before {
  content: "📋";
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
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
  .board-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .topics-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .topics-search input {
    width: 100%;
  }
  
  .topic-author-col, 
  .topic-stats-col, 
  .topic-last-post-col,
  .topic-author-cell, 
  .topic-stats-cell, 
  .topic-last-post-cell {
    display: none;
  }
  
  .topic-title-col {
    width: 100%;
  }
}

/* 标签相关样式 */
.tags-input-container {
  display: flex;
  flex-wrap: wrap;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 5px;
  gap: 5px;
  min-height: 42px;
}

.tag-item {
  display: flex;
  align-items: center;
  background-color: #e1f5fe;
  color: #0288d1;
  border-radius: 20px;
  padding: 4px 10px;
  font-size: 14px;
}

.tag-remove {
  margin-left: 6px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  color: #0288d1;
}

.tag-remove:hover {
  color: #01579b;
}

.tag-input {
  border: none;
  outline: none;
  flex: 1;
  min-width: 100px;
  padding: 6px 4px;
  font-size: 14px;
}

.tags-helper {
  margin-top: 5px;
  font-size: 12px;
  color: #666;
}
</style> 