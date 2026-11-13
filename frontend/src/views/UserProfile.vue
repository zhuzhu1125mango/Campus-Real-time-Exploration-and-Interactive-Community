<template>
  <div class="user-profile-page container-wide page-padding">
    <SectionHeader
      title="用户主页"
      icon="i-ep-user-filled"
    />

    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <template v-else>
      <!-- 用户基本信息、统计、活跃板块 -->
      <GlassCard :hover="false" class="profile-info-card">
        <div class="user-header">
          <div class="avatar-container">
            <img v-if="user.avatar" :src="user.avatar" alt="用户头像" class="user-avatar" />
            <div v-else class="avatar-placeholder">
              <span class="i-ep-user avatar-icon" />
            </div>
          </div>
          <div class="user-info">
            <h1 class="username">{{ user.username }}</h1>
            <div class="user-meta">
              <span class="join-date">
                <span class="i-ep-calendar meta-icon" />
                注册于 {{ formatDate(stats.join_date) }}
              </span>
              <span v-if="user.location" class="location">
                <span class="i-ep-location meta-icon" />
                {{ user.location }}
              </span>
            </div>
            <div class="user-bio" v-if="user.bio">{{ user.bio }}</div>
          </div>
          <FollowButton
            v-if="showFollowButton"
            :user-id="user.id"
            :following="user.is_following"
            size="md"
            @update="handleFollowUpdate"
          />
        </div>

        <!-- 用户统计信息 -->
        <div class="user-stats">
          <div class="stat-item">
            <div class="stat-value">{{ stats.topic_count }}</div>
            <div class="stat-label">主题</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ stats.post_count }}</div>
            <div class="stat-label">帖子</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ stats.reply_count }}</div>
            <div class="stat-label">回复</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ user.following_count ?? 0 }}</div>
            <div class="stat-label">关注</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ user.follower_count ?? 0 }}</div>
            <div class="stat-label">粉丝</div>
          </div>
        </div>

        <!-- 活跃板块 -->
        <div class="active-boards" v-if="stats.active_boards && stats.active_boards.length > 0">
          <h3 class="section-title">
            <span class="i-ep-grid section-icon" />
            活跃板块
          </h3>
          <div class="boards-list">
            <router-link
              v-for="board in stats.active_boards"
              :key="board.id"
              :to="`/forum/board/${board.id}`"
              class="board-item"
            >
              <span class="board-name">{{ board.name }}</span>
              <span class="board-post-count">{{ board.post_count }} 篇帖子</span>
            </router-link>
          </div>
        </div>
      </GlassCard>

      <!-- 内容标签页与列表 -->
      <GlassCard :hover="false" class="content-card">
        <div class="content-tabs">
          <div
            class="tab-item"
            :class="{ active: activeTab === 'topics' }"
            @click="setActiveTab('topics')"
          >
            <span class="i-ep-document tab-icon" />
            主题
          </div>
          <div
            class="tab-item"
            :class="{ active: activeTab === 'posts' }"
            @click="setActiveTab('posts')"
          >
            <span class="i-ep-chat-dot-round tab-icon" />
            回复
          </div>
        </div>

        <!-- 主题列表 -->
        <div v-if="activeTab === 'topics'" class="topics-list">
          <div v-if="loadingTopics" class="loading-state small">
            <div class="loading-spinner"></div>
            <p>加载中...</p>
          </div>

          <div v-else-if="topics.length === 0" class="empty-list">
            <span class="i-ep-document empty-icon" />
            <p>暂无主题</p>
          </div>

          <div v-else class="topic-items">
            <div
              v-for="topic in topics"
              :key="topic.id"
              class="topic-item"
              @click="goToTopic(topic.id)"
            >
              <div class="topic-header">
                <h3 class="topic-title">{{ topic.title }}</h3>
                <span class="topic-date">{{ formatDate(topic.created_at) }}</span>
              </div>
              <div class="topic-footer">
                <span class="topic-board">{{ (topic as any).board_name || '未知板块' }}</span>
                <div class="topic-stats">
                  <span class="stat-views">
                    <span class="i-ep-view stat-icon" />
                    {{ topic.views || 0 }} 浏览
                  </span>
                  <span class="stat-replies">
                    <span class="i-ep-chat-dot-round stat-icon" />
                    {{ (topic.post_count || 0) - 1 }} 回复
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 主题分页 -->
          <div v-if="topicTotalPages > 1" class="pagination">
            <button
              class="btn btn-secondary"
              :disabled="topicPage === 1"
              @click="changePage('topics', topicPage - 1)"
            >
              上一页
            </button>
            <span class="page-info">{{ topicPage }} / {{ topicTotalPages }}</span>
            <button
              class="btn btn-secondary"
              :disabled="topicPage === topicTotalPages"
              @click="changePage('topics', topicPage + 1)"
            >
              下一页
            </button>
          </div>
        </div>

        <!-- 帖子列表 -->
        <div v-if="activeTab === 'posts'" class="posts-list">
          <div v-if="loadingPosts" class="loading-state small">
            <div class="loading-spinner"></div>
            <p>加载中...</p>
          </div>

          <div v-else-if="posts.length === 0" class="empty-list">
            <span class="i-ep-chat-dot-round empty-icon" />
            <p>暂无回复</p>
          </div>

          <div v-else class="post-items">
            <div
              v-for="post in posts"
              :key="post.id"
              class="post-item"
              @click="goToPost(post.topic, post.id)"
            >
              <div class="post-header">
                <div class="post-topic">回复：{{ (post as any).topic_title || '未知主题' }}</div>
                <span class="post-date">{{ formatDate(post.created_at) }}</span>
              </div>
              <div class="post-content">
                <div class="post-preview">{{ getPostPreview(post.content) }}</div>
              </div>
              <div class="post-footer">
                <div v-if="(post as any).is_edited" class="post-edited">
                  (已编辑于 {{ formatDate((post as any).edited_at || '') }})
                </div>
                <div class="post-status" v-if="(post as any).content_status !== 'approved'">
                  <span class="status-badge" :class="(post as any).content_status">
                    {{ getStatusText((post as any).content_status || 'approved') }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 帖子分页 -->
          <div v-if="postTotalPages > 1" class="pagination">
            <button
              class="btn btn-secondary"
              :disabled="postPage === 1"
              @click="changePage('posts', postPage - 1)"
            >
              上一页
            </button>
            <span class="page-info">{{ postPage }} / {{ postTotalPages }}</span>
            <button
              class="btn btn-secondary"
              :disabled="postPage === postTotalPages"
              @click="changePage('posts', postPage + 1)"
            >
              下一页
            </button>
          </div>
        </div>
      </GlassCard>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userApi } from '@/api/user'
import { stripHtml } from '@/utils/xss'
import { useUserStore } from '@/stores/userStore'
import FollowButton from '@/components/FollowButton.vue'
import GlassCard from '@/components/GlassCard.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import type { User } from '@/types/user'
import type { Topic, Post } from '@/types/forum'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 状态
const loading = ref(true)
const user = ref<User>({} as User)

interface Board {
  id: number
  name: string
  post_count: number
}

const stats = ref({
  topic_count: 0,
  post_count: 0,
  reply_count: 0,
  active_boards: [] as Board[],
  join_date: ''
})
const activeTab = ref('topics')

// 主题列表
const topics = ref<Topic[]>([])
const loadingTopics = ref(false)
const topicPage = ref(1)
const topicTotalCount = ref(0)
const topicTotalPages = ref(1)

// 帖子列表
const posts = ref<Post[]>([])
const loadingPosts = ref(false)
const postPage = ref(1)
const postTotalCount = ref(0)
const postTotalPages = ref(1)

const userId = computed(() => {
  return Array.isArray(route.params.id) ? route.params.id[0] : route.params.id || 'me'
})

const isCurrentUser = computed(() => {
  return userId.value === 'me' || Number(userId.value) === Number(userStore.user?.id)
})

const showFollowButton = computed(() => {
  return userStore.isLoggedIn && !isCurrentUser.value && user.value.id
})

// 获取用户资料
const fetchUserProfile = async () => {
  loading.value = true
  try {
    const userId = Array.isArray(route.params.id) ? route.params.id[0] : route.params.id || 'me'
    const [userResponse, statsResponse] = await Promise.all([
      userApi.getUserProfile(userId),
      userApi.getUserProfileStats(userId)
    ])

    user.value = userResponse
    stats.value = statsResponse

    // 加载主题列表
    await fetchUserTopics()

  } catch (error) {
    console.error('获取用户资料失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取用户主题
const fetchUserTopics = async () => {
  loadingTopics.value = true
  try {
    const userId = Array.isArray(route.params.id) ? route.params.id[0] : route.params.id || 'me'
    const response = await userApi.getUserTopics(userId, topicPage.value)

    topics.value = response.results
    topicTotalCount.value = response.count
    topicTotalPages.value = Math.ceil(topicTotalCount.value / 10)

  } catch (error) {
    console.error('获取用户主题失败:', error)
  } finally {
    loadingTopics.value = false
  }
}

// 获取用户帖子
const fetchUserPosts = async () => {
  loadingPosts.value = true
  try {
    const userId = Array.isArray(route.params.id) ? route.params.id[0] : route.params.id || 'me'
    const response = await userApi.getUserPosts(userId, postPage.value)

    posts.value = response.results
    postTotalCount.value = response.count
    postTotalPages.value = Math.ceil(postTotalCount.value / 10)

  } catch (error) {
    console.error('获取用户帖子失败:', error)
  } finally {
    loadingPosts.value = false
  }
}

// 关注状态更新回调
const handleFollowUpdate = (following: boolean) => {
  if (!user.value.id) return
  const prev = user.value.is_following
  user.value.is_following = following
  if (prev && !following) {
    user.value.follower_count = Math.max(0, (user.value.follower_count ?? 1) - 1)
  } else if (!prev && following) {
    user.value.follower_count = (user.value.follower_count ?? 0) + 1
  }
}

// 切换标签页
const setActiveTab = (tab: string) => {
  activeTab.value = tab

  if (tab === 'posts' && posts.value.length === 0) {
    fetchUserPosts()
  }
}

// 切换页码
const changePage = async (type: string, page: number) => {
  if (type === 'topics') {
    topicPage.value = page
    await fetchUserTopics()
  } else {
    postPage.value = page
    await fetchUserPosts()
  }
}

// 跳转到主题详情
const goToTopic = (topicId: number) => {
  router.push(`/forum/topic/${topicId}`)
}

// 跳转到帖子所在的主题
const goToPost = (topicId: number, postId: number) => {
  router.push(`/forum/topic/${topicId}#post-${postId}`)
}

// 获取帖子预览内容
const getPostPreview = (content: string) => {
  const plainText = stripHtml(content)
  return plainText.length > 100 ? plainText.substring(0, 100) + '...' : plainText
}

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': '待审核',
    'approved': '已通过',
    'rejected': '已拒绝',
    'flagged': '已标记'
  }
  return statusMap[status] || status
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
onMounted(() => {
  fetchUserProfile()
})
</script>

<style scoped>
.user-profile-page {
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

.loading-state.small {
  padding: 2.5rem 0;
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
  width: 24px;
  height: 24px;
  border-width: 2px;
  margin-bottom: 0.75rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.profile-info-card {
  margin-bottom: var(--space-5);
}

.content-card {
  overflow: hidden;
}

/* 用户头部信息 */
.user-header {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding-bottom: var(--space-6);
  margin-bottom: var(--space-6);
  border-bottom: 1px solid var(--border-color-light);
}

.avatar-container {
  flex-shrink: 0;
}

.user-avatar,
.avatar-placeholder {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: hidden;
}

.avatar-placeholder {
  background: linear-gradient(135deg, var(--primary-500), var(--primary-700));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-icon {
  width: 48px;
  height: 48px;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.username {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 var(--space-2);
  color: var(--text-primary);
  line-height: 1.3;
}

.user-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  color: var(--text-secondary);
  margin-bottom: var(--space-2);
  font-size: 0.875rem;
}

.join-date,
.location {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

.meta-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.user-bio {
  color: var(--text-secondary);
  line-height: 1.5;
}

/* 用户统计信息 */
.user-stats {
  display: flex;
  margin-bottom: var(--space-6);
  overflow: hidden;
}

.stat-item {
  flex: 1;
  padding: var(--space-4) var(--space-2);
  text-align: center;
  border-right: 1px solid var(--border-color-light);
}

.stat-item:last-child {
  border-right: none;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary-600);
  margin-bottom: var(--space-1);
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

/* 活跃板块 */
.active-boards {
  padding-top: var(--space-6);
  border-top: 1px solid var(--border-color-light);
}

.section-title {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 var(--space-4);
  color: var(--text-primary);
}

.section-icon {
  width: 18px;
  height: 18px;
  color: var(--primary-600);
}

.boards-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.board-item {
  display: flex;
  flex-direction: column;
  padding: var(--space-3) var(--space-4);
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  text-decoration: none;
  color: var(--text-primary);
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.board-item:hover {
  background: var(--primary-50);
  border-color: var(--primary-200);
}

.board-name {
  font-weight: 500;
  margin-bottom: var(--space-1);
}

.board-post-count {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

/* 内容标签页 */
.content-tabs {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-5);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border-color-light);
}

.tab-item {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.tab-icon {
  width: 16px;
  height: 16px;
}

.tab-item:hover {
  border-color: var(--primary-400);
  color: var(--primary-600);
}

.tab-item.active {
  background: var(--primary-600);
  border-color: var(--primary-600);
  color: white;
}

/* 空列表 */
.empty-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-12) 0;
  color: var(--text-secondary);
  text-align: center;
}

.empty-list .empty-icon {
  width: 56px;
  height: 56px;
  margin-bottom: var(--space-3);
  border-radius: 50%;
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.75rem;
}

/* 列表项 */
.topic-items,
.post-items {
  display: flex;
  flex-direction: column;
}

.topic-item,
.post-item {
  padding: var(--space-4) 0;
  border-bottom: 1px solid var(--border-color-light);
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.topic-item:first-child,
.post-item:first-child {
  padding-top: 0;
}

.topic-item:last-child,
.post-item:last-child {
  border-bottom: none;
}

.topic-item:hover,
.post-item:hover {
  background-color: var(--bg-tertiary);
  margin: 0 calc(-1 * var(--space-5));
  padding-left: var(--space-5);
  padding-right: var(--space-5);
}

.topic-item:first-child:hover,
.post-item:first-child:hover {
  padding-top: var(--space-4);
}

.topic-header,
.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-2);
  gap: var(--space-3);
}

.topic-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
}

.post-topic {
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
}

.topic-date,
.post-date {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  white-space: nowrap;
  flex-shrink: 0;
}

.topic-footer,
.post-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  color: var(--text-secondary);
  gap: var(--space-3);
}

.topic-board {
  background: var(--primary-50);
  color: var(--primary-700);
  padding: 0.125rem var(--space-2);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
}

.topic-stats {
  display: flex;
  gap: var(--space-3);
}

.stat-views,
.stat-replies {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

.stat-icon {
  width: 16px;
  height: 16px;
}

.post-content {
  margin-bottom: var(--space-2);
}

.post-preview {
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.post-edited {
  font-style: italic;
  color: var(--text-tertiary);
}

.status-badge {
  padding: 0.125rem var(--space-2);
  border-radius: var(--radius-sm);
  color: white;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-badge.pending {
  background-color: var(--warning-color);
}

.status-badge.rejected {
  background-color: var(--error-color);
}

.status-badge.flagged {
  background-color: var(--accent-orange);
}

/* 按钮 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
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

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: var(--space-6);
  gap: var(--space-4);
}

.page-info {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

/* 响应式 */
@media (max-width: 768px) {
  .user-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: var(--space-4);
  }

  .user-info {
    width: 100%;
  }

  .user-meta {
    justify-content: center;
  }

  .user-stats {
    flex-direction: column;
  }

  .stat-item {
    border-right: none;
    border-bottom: 1px solid var(--border-color-light);
    padding: var(--space-3) var(--space-2);
  }

  .stat-item:last-child {
    border-bottom: none;
  }

  .active-boards {
    text-align: center;
  }

  .section-title {
    justify-content: center;
  }

  .boards-list {
    justify-content: center;
  }

  .content-tabs {
    justify-content: center;
  }

  .topic-header,
  .post-header,
  .topic-footer,
  .post-footer {
    flex-direction: column;
    gap: var(--space-1);
  }

  .topic-stats {
    gap: var(--space-3);
  }

  .topic-item:hover,
  .post-item:hover {
    margin: 0 calc(-1 * var(--space-4));
    padding-left: var(--space-4);
    padding-right: var(--space-4);
  }
}
</style>
