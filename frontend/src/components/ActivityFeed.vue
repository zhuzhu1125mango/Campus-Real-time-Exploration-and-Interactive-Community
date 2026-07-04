<template>
  <div class="activity-feed">
    <div class="feed-header">
      <h2>{{ title }}</h2>
      <button class="create-activity-btn" @click="showCreateForm = true">发布动态</button>
    </div>
    
    <!-- 创建动态表单 -->
    <div v-if="showCreateForm" class="create-activity-form">
      <div class="form-header">
        <h3>发布动态</h3>
        <button class="close-btn" @click="showCreateForm = false">×</button>
      </div>
      <form @submit.prevent="createActivity">
        <div class="form-group">
          <label>动态类型</label>
          <select v-model="activityForm.activity_type" required>
            <option value="custom">自定义动态</option>
            <option value="post">发布帖子</option>
            <option value="comment">发表评论</option>
            <option value="like">点赞</option>
            <option value="follow">关注用户</option>
            <option value="enroll">报名课程</option>
            <option value="share">分享内容</option>
          </select>
        </div>
        <div class="form-group">
          <label>内容</label>
          <textarea v-model="activityForm.content" placeholder="分享你的想法..." rows="4"></textarea>
        </div>
        <div class="form-group">
          <label>是否公开</label>
          <input type="checkbox" v-model="activityForm.is_public">
        </div>
        <div class="form-actions">
          <button type="button" class="cancel-btn" @click="showCreateForm = false">取消</button>
          <button type="submit" class="submit-btn">发布</button>
        </div>
      </form>
    </div>
    
    <!-- 动态列表 -->
    <div class="activities-list">
      <div v-for="activity in activities" :key="activity.id" class="activity-item">
        <div class="activity-header">
          <div class="user-info">
            <img :src="activity.user.avatar || 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=user%20avatar%20placeholder&image_size=square'" :alt="activity.user.username" class="avatar">
            <div class="user-details">
              <h4 class="username">{{ activity.user.username }}</h4>
              <span class="activity-type">{{ getActivityTypeText(activity.activity_type) }}</span>
              <span class="time">{{ formatTime(activity.created_at) }}</span>
            </div>
          </div>
        </div>
        <div class="activity-content">
          <p>{{ activity.content }}</p>
          <div v-if="activity.target_title" class="activity-target">
            <a :href="activity.target_url" target="_blank">{{ activity.target_title }}</a>
          </div>
        </div>
        <div class="activity-actions">
          <button 
            class="action-btn like-btn" 
            :class="{ 'liked': activity.is_liked }"
            @click="toggleLike(activity.id, activity.is_liked)"
          >
            <span class="icon">❤️</span>
            <span class="count">{{ activity.likes_count }}</span>
          </button>
          <button class="action-btn comment-btn" @click="toggleComments(activity.id)">
            <span class="icon">💬</span>
            <span class="count">{{ activity.comments_count }}</span>
          </button>
        </div>
        
        <!-- 评论区域 -->
        <div v-if="showComments === activity.id" class="activity-comments">
          <div class="comments-list">
            <div v-for="comment in activity.comments" :key="comment.id" class="comment-item">
              <img :src="comment.user.avatar || 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=user%20avatar%20placeholder&image_size=square'" :alt="comment.user.username" class="avatar">
              <div class="comment-content">
                <div class="comment-header">
                  <span class="username">{{ comment.user.username }}</span>
                  <span class="time">{{ formatTime(comment.created_at) }}</span>
                </div>
                <p>{{ comment.content }}</p>
                <div v-if="comment.replies && comment.replies.length > 0" class="replies-list">
                  <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
                    <img :src="reply.user.avatar || 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=user%20avatar%20placeholder&image_size=square'" :alt="reply.user.username" class="avatar">
                    <div class="reply-content">
                      <div class="reply-header">
                        <span class="username">{{ reply.user.username }}</span>
                        <span class="time">{{ formatTime(reply.created_at) }}</span>
                      </div>
                      <p>{{ reply.content }}</p>
                    </div>
                  </div>
                </div>
                <button class="reply-btn" @click="replyToComment(comment.id)">回复</button>
              </div>
            </div>
          </div>
          <div class="comment-form">
            <img :src="currentUser?.avatar || 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=user%20avatar%20placeholder&image_size=square'" :alt="currentUser?.username" class="avatar">
            <div class="form-content">
              <textarea v-model="commentForm.content" placeholder="写下你的评论..." rows="2"></textarea>
              <div class="form-actions">
                <button type="button" class="cancel-btn" @click="commentForm = { content: '', parent: undefined }">取消</button>
                <button type="button" class="submit-btn" @click="submitComment(activity.id)">评论</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="activities.length === 0" class="no-activities">
      暂无动态，快来发布第一条动态吧！
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { userApi } from '../api/user'
import { useUserStore } from '../stores/userStore'

const props = defineProps<{
  title?: string
  feedType?: 'all' | 'feed' | 'my'
}>()

const title = props.title || '动态' 
const feedType = props.feedType || 'all'
const activities = ref<any[]>([])
const showCreateForm = ref(false)
const showComments = ref<number | null>(null)
const userStore = useUserStore()
const currentUser = computed(() => userStore.user)

const activityForm = ref({
  activity_type: 'custom',
  content: '',
  is_public: true
})

const commentForm = ref({
  content: '',
  parent: undefined as number | undefined
})

const getActivityTypeText = (type: string): string => {
  const typeMap: Record<string, string> = {
    'post': '发布了帖子',
    'comment': '发表了评论',
    'like': '点赞了内容',
    'follow': '关注了用户',
    'enroll': '报名了课程',
    'share': '分享了内容',
    'custom': '发布了动态'
  }
  return typeMap[type] || type
}

const formatTime = (timeStr: string): string => {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString()
}

const loadActivities = async () => {
  try {
    let response
    if (feedType === 'feed') {
      response = await userApi.getActivityFeed()
    } else if (feedType === 'my') {
      response = await userApi.getMyActivities()
    } else {
      response = await userApi.getActivities()
    }
    // 检查response是否存在且包含results属性
    if (response && response.results) {
      activities.value = response.results
    } else {
      // 如果response格式不正确，使用空数组
      activities.value = []
      console.error('加载动态失败: 响应格式不正确', response)
    }
  } catch (error) {
    console.error('加载动态失败:', error)
    // 发生错误时，确保activities.value是一个空数组
    activities.value = []
    // 可以在这里添加用户提示，例如使用Toast组件
    // showToast('加载动态失败，请稍后重试', 'error')
  }
}

const createActivity = async () => {
  try {
    await userApi.createActivity(activityForm.value)
    activityForm.value = {
      activity_type: 'custom',
      content: '',
      is_public: true
    }
    showCreateForm.value = false
    loadActivities()
  } catch (error) {
    console.error('发布动态失败:', error)
  }
}

const toggleLike = async (activityId: number, isLiked: boolean) => {
  try {
    if (isLiked) {
      await userApi.unlikeActivity(activityId)
    } else {
      await userApi.likeActivity(activityId)
    }
    loadActivities()
  } catch (error) {
    console.error('操作失败:', error)
  }
}

const toggleComments = async (activityId: number) => {
  if (showComments.value === activityId) {
    showComments.value = null
  } else {
    showComments.value = activityId
    // 加载评论
    const activity = activities.value.find(a => a.id === activityId)
    if (activity && !activity.comments) {
      try {
        const comments = await userApi.getActivityComments(activityId)
        activity.comments = comments
      } catch (error) {
        console.error('加载评论失败:', error)
      }
    }
  }
}

const replyToComment = (commentId: number) => {
  commentForm.value.parent = commentId
}

const submitComment = async (activityId: number) => {
  try {
    await userApi.createActivityComment({
      activity: activityId,
      content: commentForm.value.content,
      parent: commentForm.value.parent
    })
    commentForm.value = { content: '', parent: undefined }
    loadActivities()
  } catch (error) {
    console.error('发表评论失败:', error)
  }
}

onMounted(() => {
  loadActivities()
})
</script>

<style scoped>
.activity-feed {
  padding: 20px;
  max-height: 600px;
  overflow-y: auto;
}

.feed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.feed-header h2 {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.create-activity-btn {
  padding: 8px 16px;
  background: #3498db;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s ease;
}

.create-activity-btn:hover {
  background: #2980b9;
}

.create-activity-form {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 20px;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.form-header h3 {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.cancel-btn {
  padding: 8px 16px;
  background: #95a5a6;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.3s ease;
}

.cancel-btn:hover {
  background: #7f8c8d;
}

.submit-btn {
  padding: 8px 16px;
  background: #27ae60;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.3s ease;
}

.submit-btn:hover {
  background: #219a52;
}

.activities-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.activity-item {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 16px;
  transition: transform 0.3s ease;
}

.activity-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.user-details {
  flex: 1;
}

.username {
  font-size: 14px;
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.activity-type {
  font-size: 12px;
  color: #666;
  margin-right: 8px;
}

.time {
  font-size: 12px;
  color: #999;
}

.activity-content {
  margin-bottom: 12px;
  line-height: 1.5;
}

.activity-content p {
  margin-bottom: 8px;
  color: #333;
}

.activity-target {
  background: #f5f7fa;
  padding: 8px 12px;
  border-radius: 4px;
  border-left: 3px solid #3498db;
}

.activity-target a {
  color: #3498db;
  text-decoration: none;
  font-size: 14px;
}

.activity-target a:hover {
  text-decoration: underline;
}

.activity-actions {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  font-size: 14px;
  color: #666;
  cursor: pointer;
  transition: color 0.3s ease;
  padding: 4px 8px;
  border-radius: 4px;
}

.action-btn:hover {
  background: #f5f7fa;
}

.like-btn.liked {
  color: #e74c3c;
}

.activity-comments {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.comment-item {
  display: flex;
  gap: 12px;
}

.comment-content {
  flex: 1;
  background: #f5f7fa;
  padding: 12px;
  border-radius: 8px;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.comment-header .username {
  font-size: 12px;
  font-weight: bold;
  color: #333;
}

.comment-header .time {
  font-size: 10px;
  color: #999;
}

.comment-content p {
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
}

.replies-list {
  margin-top: 8px;
  margin-left: 40px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reply-item {
  display: flex;
  gap: 8px;
}

.reply-content {
  flex: 1;
  background: #e8f4f8;
  padding: 8px;
  border-radius: 6px;
}

.reply-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.reply-header .username {
  font-size: 11px;
  font-weight: bold;
  color: #333;
}

.reply-header .time {
  font-size: 9px;
  color: #999;
}

.reply-content p {
  font-size: 12px;
  color: #333;
}

.reply-btn {
  background: none;
  border: none;
  font-size: 12px;
  color: #3498db;
  cursor: pointer;
  padding: 4px 0;
}

.reply-btn:hover {
  text-decoration: underline;
}

.comment-form {
  display: flex;
  gap: 12px;
}

.comment-form .form-content {
  flex: 1;
}

.comment-form textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  resize: vertical;
  margin-bottom: 8px;
}

.comment-form .form-actions {
  justify-content: flex-end;
  gap: 8px;
}

.no-activities {
  text-align: center;
  padding: 40px;
  color: #999;
  font-size: 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

@media (max-width: 768px) {
  .activity-feed {
    padding: 10px;
  }
  
  .feed-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .create-activity-btn {
    align-self: flex-end;
  }
  
  .activity-item {
    padding: 12px;
  }
  
  .activity-actions {
    gap: 12px;
  }
  
  .comment-item {
    gap: 8px;
  }
  
  .replies-list {
    margin-left: 30px;
  }
}
</style>