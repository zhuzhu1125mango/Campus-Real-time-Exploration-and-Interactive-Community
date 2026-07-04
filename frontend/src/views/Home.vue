<template>
  <div class="home-container">
    <div class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">欢迎来到<span class="highlight">校园实时互动社区</span></h1>
        <p class="hero-subtitle">连接校园, 分享知识, 共同成长</p>
        <div class="cta-buttons">
          <router-link v-if="userStore.isLoggedIn" to="/profile" class="btn btn-primary">进入个人中心</router-link>
          <router-link v-else to="/login" class="btn btn-primary">立即加入</router-link>
          <router-link to="/forum" class="btn btn-secondary">浏览社区</router-link>
        </div>
      </div>
      <div class="hero-image">
        <div class="abstract-shape shape-1"></div>
        <div class="abstract-shape shape-2"></div>
        <div class="abstract-shape shape-3"></div>
      </div>
    </div>

    <div class="features-section">
      <h2 class="section-title">探索我们的功能</h2>
      <div class="features-grid">
        <router-link to="/events" class="feature-card">
          <div class="feature-icon news-icon"></div>
          <h3>校园动态</h3>
          <p>了解最新校园活动和公告信息</p>
        </router-link>
        <router-link to="/forum" class="feature-card">
          <div class="feature-icon community-icon"></div>
          <h3>互动交流</h3>
          <p>与校友分享经验，建立人脉关系</p>
        </router-link>
        <router-link to="/learning" class="feature-card">
          <div class="feature-icon resources-icon"></div>
          <h3>在线学习</h3>
          <p>探索课程与学习资料，提升知识技能</p>
        </router-link>
      </div>
    </div>

    <div class="activity-section">
      <h2 class="section-title">社区实时动态</h2>
      <div class="activity-container">
        <div class="activity-feed">
          <div class="feed-header">
            <h3>最新动态</h3>
            <div class="filter-tabs">
              <button class="tab active" @click="activeFilter = 'all'">全部</button>
              <button class="tab" @click="activeFilter = 'qa'">问答</button>
              <button class="tab" @click="activeFilter = 'share'">分享</button>
            </div>
          </div>
          
          <div class="feed-items">
            <div v-if="loading" class="loading-state">
              <div class="loading-spinner"></div>
              <p>加载中...</p>
            </div>
            <div v-else-if="activities.length === 0" class="no-activities">
              <p>暂无动态，快来发布第一条动态吧！</p>
            </div>
            <div v-else v-for="activity in activities" :key="activity.id" class="feed-item">
              <div class="feed-avatar">
                <img :src="activity.user?.avatar || 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=user%20avatar%20placeholder&image_size=square'" :alt="activity.user?.username">
              </div>
              <div class="feed-content">
                <div class="feed-header">
                  <span class="feed-author">{{ activity.user?.username }}</span>
                  <span class="feed-time">{{ formatTime(activity.created_at) }}</span>
                </div>
                <p class="feed-text">{{ activity.content }}</p>
                <div class="feed-actions">
                  <button class="action-btn like-btn" @click="toggleLike(activity.id)">
                    <span class="action-icon" :class="{ 'liked': activity.is_liked }">{{ activity.is_liked ? '♥' : '♡' }}</span>
                    <span>{{ activity.likes_count }}</span>
                  </button>
                  <button class="action-btn comment-btn">
                    <span class="action-icon">💬</span>
                    <span>{{ activity.comments_count }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <button class="load-more-btn" @click="loadMore" :disabled="loading || !hasMore">
            {{ loading ? '加载中...' : hasMore ? '加载更多' : '没有更多了' }}
          </button>
        </div>
        
        <div class="live-chat">
          <div class="chat-header">
            <h3>实时聊天室</h3>
            <span class="online-users">
              <ChatRoomUserCount ref="userCountRef" />
            </span>
          </div>
          <div class="chat-container">
            <ChatRoom embedded @online-users-update="updateUserCount" />
          </div>
        </div>
      </div>
    </div>

    <div class="recommendation-section">
      <RecommendationSection title="为你推荐" :limit="6" />
    </div>

    <div class="social-proof">
      <div class="testimonial">
        <p class="quote">"这个平台帮我结识了许多志同道合的朋友，让校园生活更加丰富多彩！"</p>
        <p class="author">— 计算机学院 小王</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/userStore'
import ChatRoom from '../components/ChatRoom.vue'
import ChatRoomUserCount from '../components/ChatRoomUserCount.vue'
import RecommendationSection from '../components/RecommendationSection.vue'
import { userApi } from '../api/user'
import { formatDate } from '../utils/date'

// 使用用户状态存储
const userStore = useUserStore()

// 引用在线用户计数组件
const userCountRef = ref<InstanceType<typeof ChatRoomUserCount> | null>(null)

// 活动数据
const activities = ref<any[]>([])
const loading = ref(false)
const hasMore = ref(true)
const page = ref(1)
const activeFilter = ref('all')

// 更新在线用户计数
const updateUserCount = (count: number) => {
  if (userCountRef.value) {
    userCountRef.value.updateUserCount(count)
  }
}

// 格式化时间
const formatTime = (timeString: string) => {
  return formatDate(timeString)
}

// 加载活动数据
const loadActivities = async (reset = false) => {
  if (loading.value) return
  
  if (reset) {
    page.value = 1
    activities.value = []
    hasMore.value = true
  }
  
  loading.value = true
  try {
    const response = await userApi.getActivities({
      page: page.value,
      page_size: 10,
      type: activeFilter.value === 'all' ? undefined : activeFilter.value
    })
    
    if (reset) {
      activities.value = response.results
    } else {
      activities.value = [...activities.value, ...response.results]
    }
    
    hasMore.value = response.results.length === 10
    page.value++
  } catch (error) {
    console.error('加载活动失败:', error)
    // 处理未登录的情况，显示友好的提示信息
    if (error instanceof Error && 'response' in error && error.response && (error.response as any).status === 401) {
      console.log('用户未登录，显示默认活动数据')
      // 可以在这里添加一些默认的活动数据，或者显示提示信息
    }
  } finally {
    loading.value = false
  }
}

// 加载更多
const loadMore = () => {
  if (!loading.value && hasMore.value) {
    loadActivities()
  }
}

// 切换点赞
const toggleLike = async (activityId: number) => {
  try {
    const activity = activities.value.find(a => a.id === activityId)
    if (!activity) return
    
    if (activity.is_liked) {
      await userApi.unlikeActivity(activityId)
    } else {
      await userApi.likeActivity(activityId)
    }
    
    // 更新本地状态
    activity.is_liked = !activity.is_liked
    activity.likes_count += activity.is_liked ? 1 : -1
  } catch (error) {
    console.error('切换点赞失败:', error)
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadActivities(true)
})
</script>

<style scoped>
/* 现有样式 */

/* 新增样式 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(67, 97, 238, 0.3);
  border-radius: 50%;
  border-top-color: #4361ee;
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.no-activities {
  text-align: center;
  padding: 3rem;
  color: #999;
}

.action-btn.liked {
  color: #4361ee;
}

.action-btn.liked .action-icon {
  color: #4361ee;
}
</style>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.hero-section {
  display: flex;
  align-items: center;
  min-height: 80vh;
  padding: 2rem 0;
  position: relative;
  overflow: hidden;
}

.hero-content {
  flex: 1;
  z-index: 2;
}

.hero-title {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 1rem;
  line-height: 1.2;
  color: #333;
}

.highlight {
  color: #4361ee;
  position: relative;
}

.highlight::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 6px;
  background-color: rgba(67, 97, 238, 0.3);
  transform: translateY(4px);
  border-radius: 4px;
}

.hero-subtitle {
  font-size: 1.5rem;
  color: #555;
  margin-bottom: 2rem;
}

.cta-buttons {
  display: flex;
  gap: 1rem;
}

.btn {
  padding: 0.8rem 1.8rem;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
  text-decoration: none;
}

.btn-primary {
  background-color: #4361ee;
  color: white;
  box-shadow: 0 4px 6px rgba(67, 97, 238, 0.3);
}

.btn-primary:hover {
  background-color: #3a56d4;
  transform: translateY(-2px);
  box-shadow: 0 6px 8px rgba(67, 97, 238, 0.4);
}

.btn-secondary {
  background-color: white;
  color: #4361ee;
  border: 2px solid #4361ee;
}

.btn-secondary:hover {
  background-color: #f0f3ff;
  transform: translateY(-2px);
}

.hero-image {
  flex: 1;
  position: relative;
  min-height: 400px;
}

.abstract-shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.8;
}

.shape-1 {
  background: linear-gradient(135deg, #4361ee, #3a56d4);
  width: 300px;
  height: 300px;
  top: 10%;
  right: 10%;
  animation: float 8s ease-in-out infinite;
}

.shape-2 {
  background: linear-gradient(135deg, #4cc9f0, #4895ef);
  width: 200px;
  height: 200px;
  top: 50%;
  right: 25%;
  animation: float 6s ease-in-out infinite 1s;
}

.shape-3 {
  background: linear-gradient(135deg, #560bad, #7209b7);
  width: 150px;
  height: 150px;
  bottom: 15%;
  right: 15%;
  animation: float 7s ease-in-out infinite 0.5s;
}

@keyframes float {
  0% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-20px);
  }
  100% {
    transform: translateY(0px);
  }
}

.features-section {
  padding: 4rem 0;
}

.section-title {
  text-align: center;
  font-size: 2rem;
  margin-bottom: 3rem;
  color: #333;
  position: relative;
}

.section-title::after {
  content: '';
  position: absolute;
  width: 80px;
  height: 4px;
  background-color: #4361ee;
  bottom: -12px;
  left: 50%;
  transform: translateX(-50%);
  border-radius: 2px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.feature-card {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  text-align: center;
}

.feature-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.12);
}

.feature-icon {
  width: 70px;
  height: 70px;
  margin: 0 auto 1.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-position: center;
  background-size: 40px;
  background-repeat: no-repeat;
}

.news-icon {
  background-color: rgba(67, 97, 238, 0.1);
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M19 5v14H5V5h14m0-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>');
}

.community-icon {
  background-color: rgba(76, 201, 240, 0.1);
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234895ef"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>');
}

.resources-icon {
  background-color: rgba(114, 9, 183, 0.1);
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%237209b7"><path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 9H9V9h10v2zm-4 4H9v-2h6v2zm4-8H9V5h10v2z"/></svg>');
}

.feature-card h3 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: #333;
}

.feature-card p {
  color: #666;
  line-height: 1.6;
}

.activity-section {
  padding: 4rem 0;
  margin-top: 2rem;
}

.activity-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-top: 2rem;
}

/* 动态信息流样式 */
.activity-feed {
  background-color: white;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.feed-header {
  padding: 1.5rem;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.feed-header h3 {
  margin: 0;
  font-size: 1.3rem;
  color: #333;
}

.filter-tabs {
  display: flex;
  gap: 0.5rem;
}

.tab {
  background: none;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.tab.active {
  background-color: rgba(67, 97, 238, 0.1);
  color: #4361ee;
  font-weight: 600;
}

.tab:hover:not(.active) {
  background-color: #f5f5f5;
}

.feed-items {
  padding: 1rem 1.5rem;
}

.feed-item {
  display: flex;
  padding: 1.2rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.feed-item:last-child {
  border-bottom: none;
}

.feed-avatar {
  width: 50px;
  height: 50px;
  margin-right: 1rem;
  border-radius: 50%;
  overflow: hidden;
}

.feed-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.feed-content {
  flex: 1;
}

.feed-content .feed-header {
  padding: 0;
  margin-bottom: 0.5rem;
  border: none;
}

.feed-author {
  font-weight: 600;
  color: #333;
}

.feed-time {
  font-size: 0.8rem;
  color: #888;
}

.feed-text {
  margin-bottom: 1rem;
  color: #444;
  line-height: 1.5;
}

.feed-actions {
  display: flex;
  gap: 1rem;
}

.action-btn {
  background: none;
  border: none;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  color: #777;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0.3rem 0.5rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.action-btn:hover {
  background-color: #f5f5f5;
}

.load-more-btn {
  width: 100%;
  padding: 1rem;
  border: none;
  background-color: #f8f9ff;
  color: #4361ee;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.load-more-btn:hover {
  background-color: #f0f3ff;
}

/* 实时聊天样式 */
.live-chat {
  background-color: white;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
  height: auto;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.chat-header {
  padding: 1.5rem;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: white;
}

.chat-header h3 {
  margin: 0;
  font-size: 1.3rem;
  color: #333;
}

.online-users {
  color: #4361ee;
  font-size: 0.9rem;
  font-weight: 600;
}

.chat-container {
  flex: 1;
  overflow: hidden;
  min-height: 390px; /* 确保聊天容器有最小高度 */
  height: 100%;
}

/* 覆盖ChatRoom组件中的样式 */
.chat-container :deep(.chat-room) {
  border-radius: 0;
  box-shadow: none;
  height: 100%;
}

.chat-container :deep(.chat-header h3) {
  display: none; /* 只隐藏标题文字，保留放大按钮 */
}

.chat-container :deep(.chat-header .online-users) {
  display: none; /* 隐藏在线人数显示，避免重复 */
}

.chat-container :deep(.chat-input button) {
  background-color: #4361ee;
}

.chat-container :deep(.chat-input button:hover:not(:disabled)) {
  background-color: #3a56d4;
}

.chat-container :deep(.login-tip a), 
.chat-container :deep(.reconnect-btn) {
  color: #4361ee;
}

.chat-container :deep(.message-mine .message-content) {
  background-color: rgba(67, 97, 238, 0.1);
}

@media (max-width: 768px) {
  .activity-container {
    grid-template-columns: 1fr;
  }
  
  .live-chat {
    height: 450px; /* 在移动设备上稍微降低高度 */
  }
}

.recommendation-section {
  padding: 4rem 0;
}

.social-proof {
  padding: 3rem 0 5rem;
  text-align: center;
}

.testimonial {
  max-width: 800px;
  margin: 0 auto;
  background-color: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
}

.quote {
  font-size: 1.4rem;
  font-style: italic;
  color: #555;
  position: relative;
  margin-bottom: 1.5rem;
}

.quote::before, .quote::after {
  content: '"';
  font-size: 2rem;
  color: #4361ee;
  font-family: serif;
}

.author {
  font-weight: 600;
  color: #333;
}

@media (max-width: 768px) {
  .hero-section {
    flex-direction: column;
    text-align: center;
  }
  
  .hero-content {
    order: 2;
    margin-top: 2rem;
  }
  
  .hero-image {
    order: 1;
  }
  
  .cta-buttons {
    justify-content: center;
  }
  
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-subtitle {
    font-size: 1.2rem;
  }

  .shape-1, .shape-2, .shape-3 {
    transform: scale(0.7);
  }
}
</style>