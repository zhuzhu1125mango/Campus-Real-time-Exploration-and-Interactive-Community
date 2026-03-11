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
        <div class="feature-card">
          <div class="feature-icon news-icon"></div>
          <h3>校园动态</h3>
          <p>了解最新校园活动和公告信息</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon community-icon"></div>
          <h3>互动交流</h3>
          <p>与校友分享经验，建立人脉关系</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon resources-icon"></div>
          <h3>资源共享</h3>
          <p>获取学习资料，分享实用技巧</p>
        </div>
      </div>
    </div>

    <div class="activity-section">
      <h2 class="section-title">社区实时动态</h2>
      <div class="activity-container">
        <div class="activity-feed">
          <div class="feed-header">
            <h3>最新动态</h3>
            <div class="filter-tabs">
              <button class="tab active">全部</button>
              <button class="tab">问答</button>
              <button class="tab">分享</button>
            </div>
          </div>

          <div class="feed-items">
            <div class="feed-item">
              <div class="feed-avatar">
                <img src="https://randomuser.me/api/portraits/women/44.jpg" alt="用户头像">        
              </div>
              <div class="feed-content">
                <div class="feed-header">
                  <span class="feed-author">李小明</span>
                  <span class="feed-time">刚刚</span>
                </div>
                <p class="feed-text">有谁知道明天的编程比赛具体在哪个教室举行吗？</p>
                <div class="feed-actions">
                  <button class="action-btn like-btn">
                    <span class="action-icon">♥</span>
                    <span>12</span>
                  </button>
                  <button class="action-btn comment-btn">
                    <span class="action-icon">💬</span>
                    <span>8</span>
                  </button>
                </div>
              </div>
            </div>

            <div class="feed-item">
              <div class="feed-avatar">
                <img src="https://randomuser.me/api/portraits/men/32.jpg" alt="用户头像">
              </div>
              <div class="feed-content">
                <div class="feed-header">
                  <span class="feed-author">王教授</span>
                  <span class="feed-time">10分钟前</span>
                </div>
                <p class="feed-text">刚分享了一份关于云计算最新技术的资料，感兴趣的同学可以在资源区查看。</p>
                <div class="feed-actions">
                  <button class="action-btn like-btn">
                    <span class="action-icon">♥</span>
                    <span>32</span>
                  </button>
                  <button class="action-btn comment-btn">
                    <span class="action-icon">💬</span>
                    <span>14</span>
                  </button>
                </div>
              </div>
            </div>

            <div class="feed-item">
              <div class="feed-avatar">
                <img src="https://randomuser.me/api/portraits/women/68.jpg" alt="用户头像">        
              </div>
              <div class="feed-content">
                <div class="feed-header">
                  <span class="feed-author">张同学</span>
                  <span class="feed-time">30分钟前</span>
                </div>
                <p class="feed-text">我整理了一份考研复习资料，希望对大家有所帮助！</p>
                <div class="feed-actions">
                  <button class="action-btn like-btn">
                    <span class="action-icon">♥</span>
                    <span>56</span>
                  </button>
                  <button class="action-btn comment-btn">
                    <span class="action-icon">💬</span>
                    <span>23</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <button class="load-more-btn">加载更多</button>
        </div>

        <!-- 使用新的聊天室组件替换旧的聊天区域 -->
        <ChatRoom />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/userStore'
import ChatRoom from '@/components/ChatRoom.vue'

// 使用用户状态存储
const userStore = useUserStore()

// 模拟数据和功能，实际项目中会通过API获取
const online = ref(42)
</script>

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
</style> 