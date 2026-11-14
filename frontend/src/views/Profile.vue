<template>
  <div class="profile-page container-wide page-padding">
    <SectionHeader
      title="个人中心"
      :subtitle="form.username ? `欢迎回来，${form.username}` : '管理你的个人资料与账号'"
      icon="i-ep-user"
    />

    <GlassCard :hover="false" class="profile-header-card" padding="none">
      <div class="profile-banner" :style="bannerStyle">
        <label for="banner-upload" class="banner-change">
          <input
            id="banner-upload"
            type="file"
            accept="image/*"
            @change="handleBannerChange"
            hidden
          />
          <span class="i-ep-camera" />
          更换背景图
        </label>
      </div>
      <div class="profile-header-body">
        <div class="profile-avatar-wrapper">
          <div class="profile-avatar" :style="avatarStyle">
            <label for="avatar-upload" class="avatar-change">
              <input
                id="avatar-upload"
                type="file"
                accept="image/*"
                @change="handleAvatarChange"
                hidden
              />
              <span class="i-ep-camera" />
              更换头像
            </label>
          </div>
        </div>
        <h1 class="profile-name">{{ form.username }}</h1>
        <p class="profile-bio">{{ form.bio || '这个人很懒，还没有填写个人简介' }}</p>
      </div>
    </GlassCard>

    <div class="profile-tabs-bar">
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'profile' }"
        @click="activeTab = 'profile'"
      >
        <span class="i-ep-user" />
        个人资料
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'activity' }"
        @click="activeTab = 'activity'"
      >
        <span class="i-ep-view" />
        我的动态
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'friends' }"
        @click="activeTab = 'friends'"
      >
        <span class="i-ep-user-filled" />
        我的好友
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'favorites' }"
        @click="activeTab = 'favorites'"
      >
        <span class="i-ep-star" />
        收藏学校
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'settings' }"
        @click="activeTab = 'settings'"
      >
        <span class="i-ep-setting" />
        账号设置
      </button>
    </div>

    <div class="profile-panels">
      <GlassCard v-if="activeTab === 'profile'" :hover="false" title="个人资料">
        <form @submit.prevent="handleUpdate" class="profile-form">
          <div class="form-group">
            <label for="username">用户名</label>
            <div class="input-wrapper">
              <span class="input-icon i-ep-user" />
              <input
                type="text"
                id="username"
                v-model="form.username"
                required
                placeholder="请输入用户名"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="email">邮箱</label>
            <div class="input-wrapper">
              <span class="input-icon i-ep-message" />
              <input
                type="email"
                id="email"
                v-model="form.email"
                required
                placeholder="请输入邮箱"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="phone">手机号</label>
            <div class="input-wrapper">
              <span class="input-icon i-ep-phone" />
              <input
                type="tel"
                id="phone"
                v-model="form.phone"
                placeholder="请输入手机号"
                pattern="^1[3-9]\d{9}$"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="bio">个人简介</label>
            <textarea
              id="bio"
              v-model="form.bio"
              rows="4"
              placeholder="请输入个人简介"
              class="bio-textarea"
            ></textarea>
          </div>

          <div class="form-actions">
            <button type="submit" class="btn btn-primary" :disabled="loading">
              <span v-if="loading" class="loading-spinner" />
              <span>{{ loading ? '保存中...' : '保存修改' }}</span>
            </button>
          </div>
        </form>
      </GlassCard>

      <GlassCard v-if="activeTab === 'activity'" :hover="false">
        <template #header>
          <div class="panel-header">
            <h2 class="panel-title">我的动态</h2>
            <div class="panel-actions">
              <button class="btn btn-primary" @click="navigateToPublishActivity">
                <span class="i-ep-plus" />
                发布动态
              </button>
              <button
                v-if="activities.length > 0"
                @click="clearAllActivities"
                class="btn btn-danger"
              >
                <span class="i-ep-delete" />
                清除所有动态
              </button>
            </div>
          </div>
        </template>

        <div class="activity-list">
          <div v-if="activitiesLoading" class="loading-container">
            <div class="loading-spinner" />
            <p>加载中...</p>
          </div>

          <div class="empty-state" v-else-if="activities.length === 0">
            <div class="empty-icon">
              <span class="i-ep-view" />
            </div>
            <p class="empty-text">未发表任何动态</p>
          </div>

          <div v-else class="activity-items">
            <div class="activity-item" v-for="activity in activities" :key="activity.id">
              <div class="activity-time">{{ formatTime(activity.time) }}</div>
              <div class="activity-content">
                <div class="activity-type">
                  <span :class="{
                    'i-ep-document': activity.type === 'post',
                    'i-ep-chat-dot-round': activity.type === 'comment',
                    'i-ep-thumb': activity.type === 'like',
                    'i-ep-user': activity.type === 'follow',
                    'i-ep-medal': activity.type === 'enroll',
                    'i-ep-share': activity.type === 'share',
                    'i-ep-more': !['post', 'comment', 'like', 'follow', 'enroll', 'share'].includes(activity.type)
                  }" />
                  {{ activity.type === 'post' ? '发布帖子' : activity.type === 'comment' ? '发表评论' : activity.type === 'like' ? '点赞' : activity.type === 'follow' ? '关注用户' : activity.type === 'enroll' ? '报名课程' : activity.type === 'share' ? '分享内容' : '自定义动态' }}
                </div>
                <p class="activity-text">{{ activity.content }}</p>
                <div class="activity-footer">
                  <span class="activity-stat">
                    <span class="i-ep-thumb" />
                    {{ activity.likes }} 人点赞
                  </span>
                  <span class="activity-stat">
                    <span class="i-ep-chat-dot-round" />
                    {{ activity.comments }} 条评论
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </GlassCard>

      <GlassCard v-if="activeTab === 'favorites'" :hover="false" title="收藏学校">
        <div class="favorites-list">
          <div class="empty-state" v-if="favoriteSchools.length === 0">
            <div class="empty-icon">
              <span class="i-ep-star" />
            </div>
            <p class="empty-text">您还没有收藏任何学校</p>
            <div class="mt-4">
              <router-link to="/schools" class="btn btn-primary">前往浏览学校</router-link>
            </div>
          </div>

          <div v-else class="school-grid">
            <div class="school-card" v-for="school in favoriteSchools" :key="school.id">
              <div class="school-image" :style="{ backgroundImage: `url(${school.image || defaultSchoolImage})` }"></div>
              <div class="school-info">
                <h3 class="school-name">{{ school.name }}</h3>
                <p class="school-location">
                  <span class="i-ep-location" />
                  {{ school.location }}
                </p>
              </div>
              <div class="school-actions">
                <router-link :to="`/schools/${school.id}`" class="btn btn-primary">查看详情</router-link>
                <button @click="removeFavorite(school.id)" class="btn btn-icon btn-danger" title="移除收藏">
                  <span class="i-ep-delete" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </GlassCard>

      <GlassCard v-if="activeTab === 'friends'" :hover="false" title="我的好友">
        <div class="friend-search">
          <div class="input-wrapper search-wrapper">
            <span class="input-icon i-ep-search" />
            <input
              type="text"
              v-model="searchQuery"
              placeholder="搜索好友..."
              class="search-input"
            />
            <button @click="searchUsers" class="btn btn-primary search-btn">搜索</button>
          </div>
        </div>

        <div v-if="searchResults.length > 0" class="search-results">
          <h3>搜索结果</h3>
          <div class="user-list">
            <div v-for="user in searchResults" :key="user.id" class="user-item">
              <div class="user-avatar">
                <img :src="user.avatar || `${config.media.baseUrl}${config.media.defaultAvatar}`" :alt="user.username">
              </div>
              <div class="user-info">
                <div class="user-name">{{ user.username }}</div>
                <div class="user-email">{{ user.email }}</div>
              </div>
              <button @click="sendFriendRequest(user.id, user.username)" class="btn btn-primary">
                <span class="i-ep-plus" />
                添加好友
              </button>
            </div>
          </div>
        </div>

        <div v-if="friendRequests.length > 0" class="friend-requests">
          <h3>好友请求</h3>
          <div class="request-list">
            <div v-for="request in friendRequests" :key="request.id" class="request-item">
              <div class="user-avatar">
                <img :src="request.sender.avatar || `${config.media.baseUrl}${config.media.defaultAvatar}`" :alt="request.sender.username">
              </div>
              <div class="user-info">
                <div class="user-name">{{ request.sender.username }}</div>
                <div class="request-time">{{ formatTime(request.created_at) }}</div>
              </div>
              <div class="request-actions">
                <button @click="acceptFriendRequest(request.id)" class="btn btn-primary">
                  <span class="i-ep-check" />
                  接受
                </button>
                <button @click="rejectFriendRequest(request.id)" class="btn btn-secondary">
                  <span class="i-ep-close" />
                  拒绝
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="friends-list">
          <h3>好友列表</h3>
          <div v-if="friends.length === 0" class="empty-state compact">
            <div class="empty-icon">
              <span class="i-ep-user" />
            </div>
            <p class="empty-text">您还没有好友，开始添加好友吧！</p>
          </div>
          <div v-else class="friend-grid">
            <div v-for="friend in friends" :key="friend.id" class="friend-card">
              <div class="friend-avatar">
                <img :src="friend.avatar || `${config.media.baseUrl}${config.media.defaultAvatar}`" :alt="friend.username">
              </div>
              <div class="friend-info">
                <h4 class="friend-name">{{ friend.username }}</h4>
                <p class="friend-email">{{ friend.email }}</p>
              </div>
              <div class="friend-actions">
                <button @click="startChat(friend)" class="btn btn-primary">
                  <span class="i-ep-chat-dot-round" />
                  聊天
                </button>
                <button @click="removeFriend(friend.id)" class="btn btn-danger">
                  <span class="i-ep-delete" />
                  删除好友
                </button>
              </div>
            </div>
          </div>
        </div>
      </GlassCard>

      <GlassCard v-if="activeTab === 'settings'" :hover="false" title="账号设置">
        <div class="settings-group">
          <h3>
            <span class="i-ep-lock" />
            密码修改
          </h3>
          <div class="form-group">
            <label for="old-password">当前密码</label>
            <div class="input-wrapper">
              <span class="input-icon i-ep-lock" />
              <input
                :type="showOldPassword ? 'text' : 'password'"
                id="old-password"
                v-model="passwordForm.oldPassword"
                placeholder="请输入当前密码"
              />
              <button
                type="button"
                class="btn-toggle-password"
                @click="showOldPassword = !showOldPassword"
              >
                <span :class="showOldPassword ? 'i-ep-view' : 'i-ep-hide'" />
              </button>
            </div>
          </div>

          <div class="form-group">
            <label for="new-password">新密码</label>
            <div class="input-wrapper">
              <span class="input-icon i-ep-lock" />
              <input
                :type="showNewPassword ? 'text' : 'password'"
                id="new-password"
                v-model="passwordForm.newPassword"
                placeholder="请输入新密码"
                minlength="8"
              />
              <button
                type="button"
                class="btn-toggle-password"
                @click="showNewPassword = !showNewPassword"
              >
                <span :class="showNewPassword ? 'i-ep-view' : 'i-ep-hide'" />
              </button>
            </div>
          </div>

          <div class="form-group">
            <label for="confirm-password">确认新密码</label>
            <div class="input-wrapper">
              <span class="input-icon i-ep-lock" />
              <input
                :type="showConfirmPassword ? 'text' : 'password'"
                id="confirm-password"
                v-model="passwordForm.confirmPassword"
                placeholder="请再次输入新密码"
                minlength="8"
              />
              <button
                type="button"
                class="btn-toggle-password"
                @click="showConfirmPassword = !showConfirmPassword"
              >
                <span :class="showConfirmPassword ? 'i-ep-view' : 'i-ep-hide'" />
              </button>
            </div>
          </div>

          <div class="form-actions">
            <button @click="changePassword" class="btn btn-primary" :disabled="pwdLoading">
              <span v-if="pwdLoading" class="loading-spinner" />
              <span>{{ pwdLoading ? '修改中...' : '修改密码' }}</span>
            </button>
          </div>
        </div>

        <div class="settings-group danger-zone">
          <h3>
            <span class="i-ep-warning" />
            危险操作
          </h3>
          <button @click="logoutAllDevices" class="btn btn-secondary">
            <span class="i-ep-switch-button" />
            退出所有设备
          </button>
          <button @click="deactivateAccount" class="btn btn-danger">
            <span class="i-ep-delete" />
            注销账号
          </button>
        </div>
      </GlassCard>
    </div>

    <!-- 图片裁剪弹窗 -->
    <div class="cropper-modal" v-if="showCropper">
      <GlassCard :hover="false" class="cropper-container" padding="none">
        <div class="cropper-header">
          <h3>{{ cropperType === 'avatar' ? '裁剪头像 - 自由框选截取区域' : '裁剪背景图 - 自由框选截取区域' }}</h3>
          <button class="btn-close" @click="cancelCrop">
            <span class="i-ep-close" />
          </button>
        </div>
        <div class="cropper-body">
          <vue-cropper
            ref="cropper"
            :src="cropperImg"
            :aspect-ratio="cropperOptions.aspectRatio"
            :view-mode="cropperOptions.viewMode"
            :drag-mode="cropperOptions.dragMode"
            :auto-crop-area="cropperOptions.autoCropArea"
            :movable="cropperOptions.movable"
            :zoomable="cropperOptions.zoomable"
            :zoom-on-touch="cropperOptions.zoomOnTouch"
            :zoom-on-wheel="cropperOptions.zoomOnWheel"
            :wheel-zoom-ratio="cropperOptions.wheelZoomRatio"
            :guides="cropperOptions.guides"
            :center="cropperOptions.center"
            :highlight="cropperOptions.highlight"
            :background="cropperOptions.background"
            :modal="cropperOptions.modal"
            :crop-box-movable="cropperOptions.cropBoxMovable"
            :crop-box-resizable="cropperOptions.cropBoxResizable"
            :min-crop-box-width="cropperOptions.minCropBoxWidth"
            :min-crop-box-height="cropperOptions.minCropBoxHeight"
            alt="图片裁剪预览"
            @ready="onCropperCreated"
          />
          <div class="cropper-controls">
            <button class="control-btn" @click="zoomIn" title="放大">
              <span class="i-ep-zoom-in" />
            </button>
            <button class="control-btn" @click="zoomOut" title="缩小">
              <span class="i-ep-zoom-out" />
            </button>
            <button class="control-btn" @click="rotateLeft" title="向左旋转">
              <span class="i-ep-refresh-left" />
            </button>
            <button class="control-btn" @click="rotateRight" title="向右旋转">
              <span class="i-ep-refresh-right" />
            </button>
            <button class="control-btn" @click="resetCropper" title="重置">
              <span class="i-ep-refresh" />
            </button>
          </div>
          <div class="cropper-instructions">
            <p>您可以通过拖拽裁剪框四角或边缘调整大小，拖拽裁剪框内部移动位置</p>
            <p>使用上方按钮可放大、缩小、旋转图片或重置裁剪</p>
          </div>
        </div>
        <div class="cropper-footer">
          <button class="btn btn-secondary" @click="cancelCrop">取消</button>
          <button class="btn btn-primary" @click="confirmCrop">确认</button>
        </div>
      </GlassCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { logger } from '@/utils/logger'
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { userApi } from '../api/user'
import { useToast } from '../composables/useToast'
import config from '../utils/config'
// @ts-ignore 忽略类型检查错误
import VueCropper from 'vue-cropperjs'
// 使用本地CSS文件
import '../assets/cropper.css'
import { useUserStore } from '../stores/userStore'
import { ElMessage } from 'element-plus'
import { getApiErrorMessage } from '../utils/error'
import SectionHeader from '@/components/SectionHeader.vue'
import GlassCard from '@/components/GlassCard.vue'
import type { User, FriendRequest } from '../types/user'


// 获取用户Store
const userStore = useUserStore()

// 获取路由器实例
const router = useRouter()

// 基本数据
const loading = ref(false)
const pwdLoading = ref(false)
const activeTab = ref('profile')
const avatarPreview = ref('')
const bannerPreview = ref('')
const avatarFile = ref<File | null>(null) // 保存上传的头像文件引用
const bannerFile = ref<File | null>(null) // 保存上传的背景图文件引用
const { showToast } = useToast()

// 图片裁剪相关
const showCropper = ref(false)
const cropperImg = ref('')
const cropper = ref<InstanceType<typeof VueCropper> | null>(null)
const cropperType = ref<'avatar' | 'banner'>('avatar')
const cropperOptions = computed(() => {
  return {
    aspectRatio: cropperType.value === 'avatar' ? 1 : 16 / 9, // 根据类型动态设置宽高比
    viewMode: 1, // 限制裁剪框不超出图片的画布
    dragMode: 'crop', // 允许创建新的裁剪框
    autoCropArea: 0.8, // 裁剪区域大小为画布的80%
    movable: true, // 图片可移动
    zoomable: true, // 图片可缩放
    zoomOnTouch: true, // 触摸缩放
    zoomOnWheel: true, // 鼠标滚轮缩放
    wheelZoomRatio: 0.1, // 滚轮缩放比例更精细
    guides: true, // 显示网格线
    center: true, // 显示中心标记
    highlight: false, // 不高亮显示裁剪框
    cropBoxMovable: true, // 裁剪框可移动
    cropBoxResizable: true, // 裁剪框可调整大小
    responsive: true,
    restore: false,
    minCropBoxWidth: cropperType.value === 'avatar' ? 50 : 100, // 设置最小裁剪框宽度
    minCropBoxHeight: cropperType.value === 'avatar' ? 50 : 100, // 设置最小裁剪框高度
    background: true, // 显示背景
    modal: false, // 不显示黑色模态效果（不淡化裁剪框外区域）
    checkCrossOrigin: false,
    initialAspectRatio: cropperType.value === 'avatar' ? 1 : 16 / 9, // 初始宽高比
  }
})

// 表单数据
interface ProfileForm {
  username: string
  email: string
  phone: string
  bio: string
  avatar: File | null | string
  banner: File | null | string
}

const form = ref<ProfileForm>({
  username: '',
  email: '',
  phone: '',
  bio: '',
  avatar: null,
  banner: null
})

// 密码修改表单
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 控制密码显示/隐藏状态
const showOldPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

// 收藏学校数据
interface School {
  id: number
  name: string
  location: string
  image?: string
}

interface FavoriteSchoolContent {
  id?: number
  name?: string
  province?: string
  city?: string
  image?: string
  logo?: string
}

const favoriteSchools = ref<School[]>([])
const defaultSchoolImage = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M12 3L1 9l4 2.18v6L12 21l7-3.82v-6l2-1.09V17h2V9L12 3zm6.82 6L12 12.72 5.18 9 12 5.28 18.82 9zM17 15.99l-5 2.73-5-2.73v-3.72L12 15l5-2.73v3.72z"/></svg>'

// 活动数据类型定义
interface Activity {
  id: number | string
  type: string
  content: string
  time: string
  likes: number
  comments: number
}

// 活动数据 - 初始为空，确保新用户显示未发表动态状态
const activities = ref<Activity[]>([])
const activitiesLoading = ref(false)

// 获取我的动态
const fetchMyActivities = async () => {
  activitiesLoading.value = true
  try {
    const response = await userApi.getMyActivities()
    logger.log('获取我的动态:', response)

    // 转换后端数据格式到前端格式
    activities.value = response.results.map((item: any) => ({
      type: item.activity_type || item.type || 'custom',
      content: item.content || '',
      time: item.created_at || new Date().toISOString(),
      likes: item.likes_count || item.likes || 0,
      comments: item.comments_count || item.comments || 0,
      id: item.id
    }))
  } catch (error) {
    console.error('获取我的动态失败:', error)
    activities.value = []
  } finally {
    activitiesLoading.value = false
  }
}

// 清除所有动态
const clearAllActivities = () => {
  if (confirm('确定要清除所有动态记录吗？此操作不可恢复。')) {
    activities.value = []
    showToast('所有动态记录已清除', 'success')
  }
}

// 导航到动态发布页面
const navigateToPublishActivity = () => {
  // 跳转到活动页面，默认显示我的动态标签
  router.push('/activity?tab=my')
}

// 好友相关数据
const searchQuery = ref('')
const searchResults = ref<User[]>([])
const friends = ref<User[]>([])
const friendRequests = ref<FriendRequest[]>([])
const friendsLoading = ref(false)



// 计算属性：头像样式
const avatarStyle = computed(() => {
  // 调试信息
  logger.log('头像渲染：', {
    preview: avatarPreview.value,
    avatar: form.value.avatar,
    userStoreAvatar: userStore.user?.avatar
  })

  // 优先使用本地预览（刚上传的图片）
  if (avatarPreview.value) {
    // 如果是dataURL（base64），直接使用
    if (avatarPreview.value.startsWith('data:')) {
      return { backgroundImage: `url(${avatarPreview.value})` }
    }

    // 确保是绝对路径
    let url = avatarPreview.value
    if (!url.startsWith('http') && !url.startsWith('data:')) {
      url = `${config.media.baseUrl}${url.startsWith('/') ? '' : '/'}${url}`
    }

    // 添加时间戳防止缓存
    const timestamp = new Date().getTime()
    url = url.includes('?') ? `${url.split('?')[0]}?_=${timestamp}` : `${url}?_=${timestamp}`

    logger.log('渲染头像绝对URL:', url)
    return { backgroundImage: `url(${url})` }
  }

  // 其次使用用户存储中的头像
  if (userStore.user?.avatar) {
    // 确保是绝对路径
    let url = userStore.user.avatar
    if (!url.startsWith('http') && !url.startsWith('data:')) {
      url = `${config.media.baseUrl}${url.startsWith('/') ? '' : '/'}${url}`
    }

    // 添加时间戳防止缓存
    const timestamp = new Date().getTime()
    url = url.includes('?') ? `${url.split('?')[0]}?_=${timestamp}` : `${url}?_=${timestamp}`

    logger.log('渲染用户存储头像绝对URL:', url)
    return { backgroundImage: `url(${url})` }
  }

  // 最后使用表单中的头像
  if (form.value.avatar && typeof form.value.avatar === 'string') {
    // 确保是绝对路径
    let url = form.value.avatar
    if (!url.startsWith('http') && !url.startsWith('data:')) {
      url = `${config.media.baseUrl}${url.startsWith('/') ? '' : '/'}${url}`
    }

    // 添加时间戳防止缓存
    const timestamp = new Date().getTime()
    url = url.includes('?') ? `${url.split('?')[0]}?_=${timestamp}` : `${url}?_=${timestamp}`

    logger.log('渲染表单头像绝对URL:', url)
    return { backgroundImage: `url(${url})` }
  }

  // 无头像时使用默认头像
  logger.log('无头像，使用默认头像')
  return { backgroundImage: `url(${config.media.baseUrl}${config.media.defaultAvatar})` }
})

// 计算属性：背景图样式
const bannerStyle = computed(() => {
  // 调试信息
  logger.log('背景图渲染：', {
    preview: bannerPreview.value,
    banner: form.value.banner,
    userStoreBanner: userStore.user?.banner
  })

  // 优先使用本地预览（刚上传的图片）
  if (bannerPreview.value) {
    // 如果是dataURL（base64），直接使用
    if (bannerPreview.value.startsWith('data:')) {
      return { backgroundImage: `url(${bannerPreview.value})` }
    }

    // 确保是绝对路径
    let url = bannerPreview.value
    if (!url.startsWith('http') && !url.startsWith('data:')) {
      url = `${config.media.baseUrl}${url.startsWith('/') ? '' : '/'}${url}`
    }

    // 添加时间戳防止缓存
    const timestamp = new Date().getTime()
    url = url.includes('?') ? `${url.split('?')[0]}?_=${timestamp}` : `${url}?_=${timestamp}`

    logger.log('渲染背景图绝对URL:', url)
    return { backgroundImage: `url(${url})` }
  }

  // 其次使用用户存储中的背景图
  if (userStore.user?.banner) {
    // 确保是绝对路径
    let url = userStore.user.banner
    if (!url.startsWith('http') && !url.startsWith('data:')) {
      url = `${config.media.baseUrl}${url.startsWith('/') ? '' : '/'}${url}`
    }

    // 添加时间戳防止缓存
    const timestamp = new Date().getTime()
    url = url.includes('?') ? `${url.split('?')[0]}?_=${timestamp}` : `${url}?_=${timestamp}`

    logger.log('渲染用户存储背景图绝对URL:', url)
    return { backgroundImage: `url(${url})` }
  }

  // 最后使用表单中的背景图
  if (form.value.banner && typeof form.value.banner === 'string') {
    // 确保是绝对路径
    let url = form.value.banner
    if (!url.startsWith('http') && !url.startsWith('data:')) {
      url = `${config.media.baseUrl}${url.startsWith('/') ? '' : '/'}${url}`
    }

    // 添加时间戳防止缓存
    const timestamp = new Date().getTime()
    url = url.includes('?') ? `${url.split('?')[0]}?_=${timestamp}` : `${url}?_=${timestamp}`

    logger.log('渲染表单背景图绝对URL:', url)
    return { backgroundImage: `url(${url})` }
  }

  // 无背景图时使用默认背景图
  logger.log('无背景图，使用默认背景图')
  return { backgroundImage: `url(${config.media.baseUrl}${config.media.defaultBanner})` }
})

// 获取用户资料
const fetchProfile = async () => {
  try {
    // 首先从userStore获取用户信息
    await userStore.fetchUserInfo()

    // 从userStore获取最新的用户数据
    const userData = userStore.user
    logger.log('从userStore获取的用户资料:', userData)

    if (!userData) {
      // 如果userStore中没有数据，直接从API获取
      const response = await userApi.getProfile()
      const apiUserData = response
      logger.log('从API获取的用户资料:', apiUserData)

      // 复制所有需要的字段
      form.value = {
        username: apiUserData.username || '',
        email: apiUserData.email || '',
        phone: apiUserData.phone || '',
        bio: apiUserData.bio || '',
        avatar: null, // 不直接使用URL
        banner: null  // 不直接使用URL
      }

      // 设置用户头像预览 - 直接使用完整URL
      if (apiUserData.avatar && typeof apiUserData.avatar === 'string') {
        // 记录原始数据
        logger.log('原始头像URL:', apiUserData.avatar)

        // 确保URL是完整的
        let avatarUrl = apiUserData.avatar
        if (!avatarUrl.startsWith('http') && !avatarUrl.startsWith('/')) {
          // 如果是相对路径，添加API基础URL
          const baseMediaUrl = import.meta.env.VITE_UPLOAD_URL || 'http://localhost:8000/media'
          avatarUrl = `${baseMediaUrl}/${avatarUrl}`
          logger.log('添加基础URL后:', avatarUrl)
        }

        // 添加时间戳参数防止缓存
        const timestamp = new Date().getTime()
        const newAvatarUrl = avatarUrl.includes('?')
          ? `${avatarUrl}&_=${timestamp}`
          : `${avatarUrl}?_=${timestamp}`

        logger.log('最终头像URL:', newAvatarUrl)
        avatarPreview.value = newAvatarUrl
      }

      // 设置用户背景图预览 - 直接使用完整URL
      if (apiUserData.banner && typeof apiUserData.banner === 'string') {
        logger.log('服务器返回的背景图URL:', apiUserData.banner)

        // 处理Banner URL
        let bannerUrl = apiUserData.banner

        // 确保是完整的URL
        if (typeof bannerUrl === 'string' && !bannerUrl.startsWith('http') && !bannerUrl.startsWith('/')) {
          // 相对路径，添加媒体URL前缀
          const baseMediaUrl = import.meta.env.VITE_UPLOAD_URL || 'http://localhost:8000/media'
          bannerUrl = `${baseMediaUrl}/${bannerUrl}`
        }

        // 添加时间戳参数防止缓存
        const timestamp = new Date().getTime()
        const finalBannerUrl = bannerUrl.includes('?')
          ? `${bannerUrl.split('?')[0]}?_=${timestamp}`
          : `${bannerUrl}?_=${timestamp}`

        logger.log('处理后的背景图URL:', finalBannerUrl)

        // 清除旧的Blob URL
        if (bannerPreview.value && bannerPreview.value.startsWith('blob:')) {
          URL.revokeObjectURL(bannerPreview.value)
        }

        // 立即更新背景图预览
        bannerPreview.value = finalBannerUrl
        logger.log('更新背景图预览为最新URL:', bannerPreview.value)

        // 强制触发渲染
        setTimeout(() => {
          const tempUrl = bannerPreview.value
          bannerPreview.value = ''
          setTimeout(() => {
            bannerPreview.value = tempUrl
            logger.log('刷新背景图预览完成')
          }, 50)
        }, 0)
      }
    } else {
      // 使用userStore中的数据
      form.value = {
        username: userData.username || '',
        email: userData.email || '',
        phone: userData.phone || '',
        bio: userData.bio || '',
        avatar: null, // 不直接使用URL
        banner: null  // 不直接使用URL
      }

      // 设置用户头像预览 - 直接使用完整URL
      if (userData.avatar && typeof userData.avatar === 'string') {
        // 记录原始数据
        logger.log('userStore中的头像URL:', userData.avatar)

        // 添加时间戳参数防止缓存
        const timestamp = new Date().getTime()
        const newAvatarUrl = userData.avatar.includes('?')
          ? `${userData.avatar.split('?')[0]}?_=${timestamp}`
          : `${userData.avatar}?_=${timestamp}`

        logger.log('最终头像URL:', newAvatarUrl)
        avatarPreview.value = newAvatarUrl
      }

      // 设置用户背景图预览 - 直接使用完整URL
      if (userData.banner && typeof userData.banner === 'string') {
        logger.log('userStore中的背景图URL:', userData.banner)

        // 添加时间戳参数防止缓存
        const timestamp = new Date().getTime()
        const finalBannerUrl = userData.banner.includes('?')
          ? `${userData.banner.split('?')[0]}?_=${timestamp}`
          : `${userData.banner}?_=${timestamp}`

        logger.log('处理后的背景图URL:', finalBannerUrl)

        // 清除旧的Blob URL
        if (bannerPreview.value && bannerPreview.value.startsWith('blob:')) {
          URL.revokeObjectURL(bannerPreview.value)
        }

        // 立即更新背景图预览
        bannerPreview.value = finalBannerUrl
        logger.log('更新背景图预览为最新URL:', bannerPreview.value)

        // 强制触发渲染
        setTimeout(() => {
          const tempUrl = bannerPreview.value
          bannerPreview.value = ''
          setTimeout(() => {
            bannerPreview.value = tempUrl
            logger.log('刷新背景图预览完成')
          }, 50)
        }, 0)
      }
    }

    logger.log('从profile更新userStore数据')
    await userStore.fetchUserInfo()
  } catch (error) {
    console.error('获取个人资料失败:', error)
    showToast('获取个人资料失败', 'error')
  }
}

// 读取文件并显示裁剪界面
const readAndShowCropper = (file: File) => {
  const reader = new FileReader()

  reader.onload = (e) => {
    if (e.target && e.target.result) {
      cropperImg.value = e.target.result as string
      showCropper.value = true
    }
  }

  reader.onerror = () => {
    showToast('文件读取失败，请重试', 'error')
  }

  reader.readAsDataURL(file)
}

// 选择头像
const handleAvatarChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (!input.files || !input.files[0]) return

  const file = input.files[0]

  // 验证文件类型
  if (!config.upload.allowedTypes.includes(file.type)) {
    showToast('请选择 JPG、PNG、GIF 或 WebP 格式的图片', 'error')
    input.value = '' // 清空input
    return
  }

  // 验证文件大小
  if (file.size > config.upload.maxSize) {
    showToast(`图片大小不能超过 ${config.upload.maxSize / 1024 / 1024}MB`, 'error')
    input.value = '' // 清空input
    return
  }

  // 保存文件引用
  avatarFile.value = file

  // 读取文件显示裁剪界面
  cropperType.value = 'avatar'
  readAndShowCropper(file)

  // 重置input值，确保可以选择相同文件
  input.value = ''
}

// 选择背景图
const handleBannerChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (!input.files || !input.files[0]) return

  const file = input.files[0]

  // 验证文件类型
  if (!config.upload.allowedTypes.includes(file.type)) {
    showToast('请选择 JPG、PNG、GIF 或 WebP 格式的图片', 'error')
    input.value = '' // 清空input
    return
  }

  // 验证文件大小
  if (file.size > config.upload.maxSize) {
    showToast(`图片大小不能超过 ${config.upload.maxSize / 1024 / 1024}MB`, 'error')
    input.value = '' // 清空input
    return
  }

  // 保存文件引用
  bannerFile.value = file

  // 读取文件显示裁剪界面
  cropperType.value = 'banner'
  readAndShowCropper(file)

  // 重置input值，确保可以选择相同文件
  input.value = ''
}

// 确认裁剪
const confirmCrop = async () => {
  if (!cropper.value) return

  try {
    // 获取裁剪后的canvas
    const canvas = cropper.value.getCroppedCanvas({
      minWidth: 100,
      minHeight: 100,
      maxWidth: 1000,
      maxHeight: 1000,
      fillColor: '#fff'
    })

    if (!canvas) {
      console.error('裁剪失败，无法获取裁剪后的canvas')
      showToast('裁剪失败，请重试', 'error')
      return
    }

    // 转换为data URL而不是Blob URL
    const dataUrl = canvas.toDataURL('image/jpeg', 0.9)
    logger.log('生成的DataURL开头部分:', dataUrl.substring(0, 50) + '...')

    // 转换为文件对象
    const blobBin = atob(dataUrl.split(',')[1])
    const array = []
    for (let i = 0; i < blobBin.length; i++) {
      array.push(blobBin.charCodeAt(i))
    }
    const blob = new Blob([new Uint8Array(array)], { type: 'image/jpeg' })
    logger.log('生成的Blob对象:', blob.type, blob.size, '字节')

    // 使用用户ID作为文件名的一部分，确保唯一性
    const userId = userStore.user?.id || Math.floor(Math.random() * 10000)
    let fileName = ''
    if (cropperType.value === 'avatar') {
      fileName = `avatar_${userId}_${Date.now()}.jpg`
    } else {
      fileName = `banner_${userId}_${Date.now()}.jpg`
    }

    // 创建File对象
    const newFile = new File([blob], fileName, { type: 'image/jpeg', lastModified: Date.now() })
    logger.log('创建文件成功:', fileName, newFile.size, '字节')

    // 将文件对象保存到表单
    if (cropperType.value === 'avatar') {
      form.value.avatar = newFile
      avatarPreview.value = dataUrl
      logger.log('设置头像预览:', {
        预览URL类型: typeof avatarPreview.value,
        开头: avatarPreview.value.substring(0, 30) + '...',
        form中的文件: form.value.avatar ? `是(${form.value.avatar.name})` : '否'
      })
    } else {
      form.value.banner = newFile
      bannerPreview.value = dataUrl
      logger.log('设置背景图预览:', {
        预览URL类型: typeof bannerPreview.value,
        开头: bannerPreview.value.substring(0, 30) + '...',
        form中的文件: form.value.banner ? `是(${form.value.banner.name})` : '否'
      })
    }

    // 关闭裁剪界面
    showCropper.value = false

    // 不自动保存，让用户手动点击保存按钮
    showToast('图片裁剪成功，请点击保存按钮保存更改', 'success')
  } catch (error) {
    console.error('裁剪过程出错:', error)
    showToast('裁剪过程出错，请重试', 'error')
  }
}

// 取消裁剪
const cancelCrop = () => {
  showCropper.value = false
}

// 更新个人资料
const handleUpdate = async () => {
  loading.value = true;

  try {
    logger.log('开始更新用户资料...', form.value);

    // 创建FormData对象用于上传文件
    const formData = new FormData();

    // 添加非文件字段
    for (const [key, value] of Object.entries(form.value)) {
      // 跳过文件字段，这些会单独处理
      if (key === 'avatar' || key === 'banner') continue;

      // 添加其他字段
      if (value !== null && value !== undefined) {
        formData.append(key, String(value));
      }
    }

    // 单独处理头像文件
    if (form.value.avatar) {
      logger.log('处理头像...');
      // 如果是文件对象，直接添加
      if (form.value.avatar instanceof File) {
        logger.log('头像是File对象');
        formData.append('avatar', form.value.avatar);
      }
      // 如果是Data URL，转换为文件
      else if (typeof form.value.avatar === 'string' && form.value.avatar.startsWith('data:')) {
        logger.log('头像是Data URL');
        // 使用用户ID作为文件名的一部分，确保唯一性
        const userId = userStore.user?.id || Math.floor(Math.random() * 10000);
        const avatarFile = dataURLtoFile(form.value.avatar, `avatar_${userId}_${Date.now()}.jpg`);
        formData.append('avatar', avatarFile);
      }
      // 如果是已有的URL
      else if (typeof form.value.avatar === 'string' && !form.value.avatar.startsWith('blob:')) {
        // 如果URL没有改变，不需要重新上传
        if (form.value.avatar === userStore.user?.avatar) {
          logger.log('头像URL未变更，不需要重新上传');
        } else {
          logger.log('头像是URL，需要重新上传');
          formData.append('avatar', form.value.avatar);
        }
      }
    }

    // 单独处理背景图片文件
    if (form.value.banner) {
      logger.log('处理背景图...');
      // 如果是文件对象，直接添加
      if (form.value.banner instanceof File) {
        logger.log('背景图是File对象');
        formData.append('banner', form.value.banner);
      }
      // 如果是Data URL，转换为文件
      else if (typeof form.value.banner === 'string' && form.value.banner.startsWith('data:')) {
        logger.log('背景图是Data URL');
        // 使用用户ID作为文件名的一部分，确保唯一性
        const userId = userStore.user?.id || Math.floor(Math.random() * 10000);
        const bannerFile = dataURLtoFile(form.value.banner, `banner_${userId}_${Date.now()}.jpg`);
        formData.append('banner', bannerFile);
      }
      // 如果是已有的URL
      else if (typeof form.value.banner === 'string' && !form.value.banner.startsWith('blob:')) {
        // 如果URL没有改变，不需要重新上传
        if (form.value.banner === userStore.user?.banner) {
          logger.log('背景图URL未变更，不需要重新上传');
        } else {
          logger.log('背景图是URL，需要重新上传');
          formData.append('banner', form.value.banner);
        }
      }
    }

    // 打印FormData内容供调试
    for (const pair of formData.entries()) {
      logger.log(`FormData: ${pair[0]}: ${pair[1]}`);
    }

    // 发送更新请求
    await userApi.updateProfile(formData);

    // 重新获取最新的用户数据
    await userStore.fetchUserProfile();

    // 重新加载个人资料，确保所有数据都已更新
    await fetchProfile();

    // 清除本地预览数据与 localStorage 临时缓存
    avatarPreview.value = '';
    bannerPreview.value = '';
    localStorage.removeItem('tempAvatarPreview');
    localStorage.removeItem('tempBannerPreview');

    // 显示成功消息
    ElMessage.success('个人资料更新成功');

    // 加载完成
    loading.value = false;
  } catch (error) {
    console.error('更新个人资料出错:', error);
    ElMessage.error('更新个人资料失败，请重试');
    loading.value = false;
  }
};

// 将Data URL转换为File对象
const dataURLtoFile = (dataURL: string, filename: string): File => {
  const arr = dataURL.split(',');
  const mime = arr[0].match(/:(.*?);/)![1];
  const bstr = atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);

  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }

  return new File([u8arr], filename, { type: mime });
};

// 修改密码
const changePassword = async () => {
  // 验证密码
  if (!passwordForm.value.oldPassword) {
    showToast('请输入当前密码', 'error')
    return
  }

  if (!passwordForm.value.newPassword) {
    showToast('请输入新密码', 'error')
    return
  }

  if (passwordForm.value.newPassword.length < 8) {
    showToast('新密码长度不能少于8位', 'error')
    return
  }

  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    showToast('两次输入的密码不一致', 'error')
    return
  }

  try {
    pwdLoading.value = true
    await userApi.changePassword({
      old_password: passwordForm.value.oldPassword,
      new_password: passwordForm.value.newPassword
    })
    showToast('密码修改成功', 'success')
    passwordForm.value = {
      oldPassword: '',
      newPassword: '',
      confirmPassword: ''
    }
  } catch (error) {
    console.error('密码修改失败:', error)
    showToast(getApiErrorMessage(error, '密码修改失败，请检查当前密码是否正确'), 'error')
  } finally {
    pwdLoading.value = false
  }
}

// 获取收藏的学校
const fetchFavoriteSchools = async () => {
  try {
    const favoritesResponse = await userApi.getFavoriteSchools();

    if (!favoritesResponse || !Array.isArray(favoritesResponse)) {
      console.error('获取收藏学校失败: 格式错误', favoritesResponse);
      favoriteSchools.value = [];
      return;
    }

    // 提取学校信息
    favoriteSchools.value = [];
    for (const favorite of favoritesResponse) {
      // 检查是否为学校类型的收藏
      if (favorite.content_type === 'schools.school' && favorite.content_object) {
        const school = favorite.content_object as FavoriteSchoolContent;
        favoriteSchools.value.push({
          id: school.id || favorite.object_id,
          name: school.name || favorite.content_object_name || `学校 ${favorite.object_id}`,
          location: (school.province || school.city)
            ? `${school.province || ''} ${school.city || ''}`.trim()
            : (favorite.note || '未知地区'),
          image: school.image || school.logo || undefined
        });
      } else if (favorite.content_type && favorite.content_type.includes('school') && favorite.object_id) {
        // 兼容旧数据
        favoriteSchools.value.push({
          id: favorite.object_id,
          name: favorite.content_object_name || `学校 ${favorite.object_id}`,
          location: favorite.note || '未知地区',
          image: undefined
        });
      }
    }
  } catch (error) {
    console.error('获取收藏学校失败:', error);
    showToast('获取收藏学校失败', 'error');
  }
}

// 移除收藏学校
const removeFavorite = async (schoolId: number) => {
  try {
    await userApi.removeFavoriteSchool(schoolId)
    showToast('已移除收藏', 'success')
    // 更新列表
    favoriteSchools.value = favoriteSchools.value.filter(school => school.id !== schoolId)
  } catch (error) {
    console.error('移除收藏失败:', error)
    showToast('移除收藏失败', 'error')
  }
}

// 退出所有设备
const logoutAllDevices = () => {
  if (confirm('确定要退出所有设备吗？')) {
    // 实际项目中调用API
    showToast('已退出所有设备', 'success')
  }
}

// 注销账号
const deactivateAccount = () => {
  if (confirm('注销账号是不可逆操作，确定要继续吗？')) {
    // 实际项目中调用API
    showToast('账号已注销', 'warning')
  }
}

// 好友相关方法
// 搜索用户
const searchUsers = async () => {
  if (!searchQuery.value.trim()) {
    showToast('请输入搜索关键词', 'error')
    return
  }

  try {
    const response = await userApi.searchUsers(searchQuery.value)
    searchResults.value = response
  } catch (error) {
    console.error('搜索用户失败:', error)
    showToast('搜索用户失败', 'error')
  }
}

// 发送好友请求
const sendFriendRequest = async (userId: number, username: string) => {
  try {
    await userApi.sendFriendRequest(userId)
    showToast(`已向 ${username} 发送好友请求`, 'success')
    // 清空搜索结果
    searchResults.value = []
    searchQuery.value = ''
  } catch (error) {
    console.error('发送好友请求失败:', error)
    showToast('发送好友请求失败', 'error')
  }
}

// 获取好友列表
const fetchFriends = async () => {
  try {
    friendsLoading.value = true
    const response = await userApi.getFriends()
    friends.value = response.friends || []
  } catch (error) {
    console.error('获取好友列表失败:', error)
    showToast('获取好友列表失败', 'error')
  } finally {
    friendsLoading.value = false
  }
}

// 获取好友请求
const fetchFriendRequests = async () => {
  try {
    const response = await userApi.getReceivedFriendRequests()
    friendRequests.value = response
  } catch (error) {
    console.error('获取好友请求失败:', error)
    showToast('获取好友请求失败', 'error')
  }
}

// 接受好友请求
const acceptFriendRequest = async (requestId: number) => {
  try {
    await userApi.acceptFriendRequest(requestId)
    showToast('已接受好友请求', 'success')
    // 重新获取好友列表和请求
    await fetchFriends()
    await fetchFriendRequests()
  } catch (error) {
    console.error('接受好友请求失败:', error)
    showToast('接受好友请求失败', 'error')
  }
}

// 拒绝好友请求
const rejectFriendRequest = async (requestId: number) => {
  try {
    await userApi.rejectFriendRequest(requestId)
    showToast('已拒绝好友请求', 'success')
    // 重新获取好友请求
    await fetchFriendRequests()
  } catch (error) {
    console.error('拒绝好友请求失败:', error)
    showToast('拒绝好友请求失败', 'error')
  }
}

// 删除好友
const removeFriend = async (userId: number) => {
  if (confirm('确定要删除这个好友吗？')) {
    try {
      await userApi.removeFriend(userId)
      showToast('已删除好友', 'success')
      // 重新获取好友列表
      await fetchFriends()
    } catch (error) {
      console.error('删除好友失败:', error)
      showToast('删除好友失败', 'error')
    }
  }
}

// 开始聊天
const startChat = (friend: User) => {
  router.push(`/chat/${friend.id}`)
}

// 格式化时间
const formatTime = (timeString: string) => {
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

// 添加裁剪控制方法
// 放大
const zoomIn = () => {
  if (cropper.value) {
    cropper.value.zoom(0.1)
  }
}

// 缩小
const zoomOut = () => {
  if (cropper.value) {
    cropper.value.zoom(-0.1)
  }
}

// 向左旋转
const rotateLeft = () => {
  if (cropper.value) {
    cropper.value.rotate(-90)
  }
}

// 向右旋转
const rotateRight = () => {
  if (cropper.value) {
    cropper.value.rotate(90)
  }
}

// 重置裁剪器
const resetCropper = () => {
  if (cropper.value) {
    cropper.value.reset()
  }
}

// 调整onCropperCreated函数，显示完整原图并允许用户自由截取
const onCropperCreated = () => {
  if (!cropper.value) return

  // 重置裁剪器以便准确获取数据
  cropper.value.reset()

  // 使用setTimeout确保DOM已更新，数据准确
  setTimeout(() => {
    if (!cropper.value) return

    try {
      // 清除之前的缩放和位置
      cropper.value.clear()

      // 获取容器和图片数据
      const containerData = cropper.value.getContainerData()
      const canvasData = cropper.value.getCanvasData()

      // 计算缩放比例，使图片完全可见并居中显示
      const scale = Math.min(
        (containerData.width * 0.9) / canvasData.naturalWidth,
        (containerData.height * 0.9) / canvasData.naturalHeight
      )

      // 应用缩放
      cropper.value.zoomTo(scale)

      // 重新获取调整后的画布数据
      const newCanvasData = cropper.value.getCanvasData()

      // 计算居中位置
      const offsetX = (containerData.width - newCanvasData.width) / 2
      const offsetY = (containerData.height - newCanvasData.height) / 2

      // 移动到居中位置
      cropper.value.moveTo(offsetX, offsetY)

      // 设置初始裁剪框
      const cropBoxData = {
        left: containerData.width / 2 - (containerData.width * 0.4),
        top: containerData.height / 2 - (containerData.height * 0.4),
        width: containerData.width * 0.8,
        height: cropperType.value === 'avatar'
          ? containerData.width * 0.8
          : (containerData.width * 0.8) / (16/9)
      }

      cropper.value.setCropBoxData(cropBoxData)
    } catch (err) {
      console.error('裁剪器初始化错误:', err)
      // 出错时尝试简单重置
      try {
        cropper.value.reset()
      } catch (e) {
        console.error('重置裁剪器失败:', e)
      }
    }
  }, 200) // 延长时间以确保DOM已完全加载
}

onMounted(() => {
  fetchProfile()
  fetchFavoriteSchools()
  fetchFriends()
  fetchFriendRequests()

  // 页面加载时恢复之前的预览
  if (localStorage.getItem('tempAvatarPreview')) {
    avatarPreview.value = localStorage.getItem('tempAvatarPreview') || ''
  }
  if (localStorage.getItem('tempBannerPreview')) {
    bannerPreview.value = localStorage.getItem('tempBannerPreview') || ''
  }

  // 添加调试状态
})

// 监听标签切换，当切换到对应标签时加载数据
watch(activeTab, (newTab) => {
  if (newTab === 'activity') {
    fetchMyActivities()
  } else if (newTab === 'favorites') {
    fetchFavoriteSchools()
  }
})

// 确保图片上传后的状态保持
window.addEventListener('beforeunload', () => {
  // 保存当前的头像和背景图预览到localStorage
  if (avatarPreview.value) {
    localStorage.setItem('tempAvatarPreview', avatarPreview.value)
  }
  if (bannerPreview.value) {
    localStorage.setItem('tempBannerPreview', bannerPreview.value)
  }
})

// 页面加载时恢复之前的预览
if (localStorage.getItem('tempAvatarPreview')) {
  avatarPreview.value = localStorage.getItem('tempAvatarPreview') || ''
}
if (localStorage.getItem('tempBannerPreview')) {
  bannerPreview.value = localStorage.getItem('tempBannerPreview') || ''
}

// 调试信息

</script>

<style scoped>
.profile-page {
  min-height: calc(100vh - 200px);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.panel-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

/* 按钮 */
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

.btn-danger {
  background-color: var(--error-color);
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background-color: #dc2626;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-icon {
  padding: 0.5rem;
  border-radius: var(--radius-md);
}

/* 个人资料头部 */
.profile-header-card {
  overflow: hidden;
  margin-bottom: var(--space-6);
}

.profile-banner {
  height: 260px;
  background: linear-gradient(135deg, var(--primary-500), var(--primary-700));
  background-size: cover;
  background-position: center;
  position: relative;
  width: 100%;
}

.banner-change {
  position: absolute;
  bottom: 12px;
  right: 12px;
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  border-radius: var(--radius-md);
  text-align: center;
  padding: 8px 14px;
  font-size: 0.85rem;
  cursor: pointer;
  opacity: 0.9;
  transition: opacity 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  z-index: 10;
  backdrop-filter: blur(4px);
}

.profile-banner:hover .banner-change {
  opacity: 1;
}

.banner-change:hover,
.banner-change:focus {
  opacity: 1 !important;
}

.profile-header-body {
  position: relative;
  text-align: center;
  padding: 0 var(--space-6) var(--space-6);
}

.profile-avatar-wrapper {
  position: relative;
  margin-top: -60px;
  display: flex;
  justify-content: center;
  z-index: 5;
}

.profile-avatar {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background-color: var(--primary-500);
  border: 4px solid var(--bg-primary);
  position: relative;
  background-size: cover;
  background-position: center;
  overflow: hidden;
  box-shadow: var(--shadow-md);
}

.avatar-change {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: rgba(0, 0, 0, 0.45);
  color: white;
  text-align: center;
  padding: 6px 0;
  font-size: 0.75rem;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.3s;
  z-index: 10;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.profile-avatar:hover .avatar-change {
  opacity: 1;
}

.avatar-change:hover,
.avatar-change:focus {
  opacity: 1 !important;
}

.profile-name {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 1rem 0 0.5rem;
  color: var(--text-primary);
}

.profile-bio {
  color: var(--text-secondary);
  max-width: 600px;
  margin: 0 auto;
  padding: 0 var(--space-4);
}

/* 标签页 */
.profile-tabs-bar {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-6);
  padding: var(--space-1);
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  width: fit-content;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  color: var(--text-primary);
  background: var(--bg-primary);
}

.tab-btn.active {
  background: var(--bg-primary);
  color: var(--primary-600);
  box-shadow: var(--shadow-sm);
}

.dark .tab-btn.active {
  background: var(--bg-primary);
  color: var(--primary-400);
}

/* 面板 */
.profile-panels {
  margin-bottom: var(--space-6);
}

/* 表单 */
.profile-form {
  max-width: 600px;
}

.form-group {
  margin-bottom: var(--space-5);
}

.form-group label {
  display: block;
  margin-bottom: var(--space-2);
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.9rem;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 12px;
  width: 20px;
  height: 20px;
  color: var(--text-tertiary);
  z-index: 1;
}

input,
textarea {
  width: 100%;
  padding: 0.8rem 0.8rem 0.8rem 2.5rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 1rem;
  color: var(--text-primary);
  background-color: var(--bg-primary);
  transition: all 0.2s;
}

.bio-textarea {
  padding: 0.8rem;
  resize: vertical;
}

input:focus,
textarea:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-actions {
  margin-top: var(--space-6);
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: var(--space-10) var(--space-4);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
}

.empty-state.compact {
  padding: var(--space-8) var(--space-4);
}

.empty-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
  font-size: 2rem;
}

.empty-text {
  margin: 0;
  max-width: 80%;
  text-align: center;
  color: var(--text-secondary);
  font-size: 1rem;
  font-weight: 500;
}

.mt-4 {
  margin-top: var(--space-4);
}

/* 动态 */
.activity-list {
  min-height: 300px;
}

.activity-item {
  display: flex;
  padding: var(--space-4) 0;
  border-bottom: 1px solid var(--border-color-light);
}

.activity-item:last-child {
  border: none;
}

.activity-time {
  min-width: 90px;
  color: var(--text-tertiary);
  padding-top: 0.2rem;
  font-size: 0.875rem;
}

.activity-content {
  flex: 1;
}

.activity-type {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-weight: 600;
  color: var(--primary-600);
  margin-bottom: var(--space-2);
}

.activity-text {
  margin-bottom: var(--space-3);
  color: var(--text-primary);
}

.activity-footer {
  display: flex;
  gap: var(--space-4);
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.activity-stat {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

/* 好友 */
.friend-search {
  margin-bottom: var(--space-6);
}

.search-wrapper {
  display: flex;
}

.search-input {
  flex: 1;
  padding: 0.8rem;
  border-radius: var(--radius-md) 0 0 var(--radius-md);
  border-right: none;
}

.search-btn {
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
}

.search-results,
.friend-requests {
  margin-bottom: var(--space-6);
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--border-color-light);
}

.search-results h3,
.friend-requests h3,
.friends-list h3 {
  margin-bottom: var(--space-4);
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.user-list,
.request-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.user-item,
.request-item {
  display: flex;
  align-items: center;
  padding: var(--space-3);
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  transition: all 0.2s;
}

.user-item:hover,
.request-item:hover {
  background: var(--border-color-light);
}

.user-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: var(--space-3);
  flex-shrink: 0;
  background: var(--bg-secondary);
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.15rem;
}

.user-email {
  font-size: 0.875rem;
  color: var(--text-secondary);
  word-break: break-all;
}

.request-time {
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

.request-actions {
  display: flex;
  gap: var(--space-2);
}

.friend-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--space-4);
}

.friend-card {
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.friend-card:hover {
  background: var(--border-color-light);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.friend-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  overflow: hidden;
  margin-bottom: var(--space-3);
  background: var(--bg-secondary);
}

.friend-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.friend-name {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-1);
}

.friend-email {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
  word-break: break-all;
}

.friend-actions {
  width: 100%;
  display: flex;
  gap: var(--space-2);
  justify-content: center;
}

/* 账号设置 */
.settings-group {
  margin-bottom: var(--space-8);
}

.settings-group h3 {
  font-size: 1rem;
  color: var(--text-primary);
  margin-bottom: var(--space-5);
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.danger-zone {
  border-top: 1px solid var(--border-color-light);
  padding-top: var(--space-6);
}

.danger-zone .btn {
  margin-right: var(--space-3);
  margin-bottom: var(--space-2);
}

/* 密码显示/隐藏按钮样式 */
.btn-toggle-password {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  outline: none;
}

.btn-toggle-password:hover {
  color: var(--text-secondary);
}

/* 收藏学校 */
.favorites-list {
  min-height: 200px;
}

.school-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--space-5);
  margin-top: var(--space-2);
}

.school-card {
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all 0.2s;
  border: 1px solid var(--border-color-light);
}

.school-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.school-image {
  height: 140px;
  background-color: var(--bg-secondary);
  background-size: cover;
  background-position: center;
}

.school-info {
  padding: var(--space-4);
}

.school-name {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: var(--space-1);
  color: var(--text-primary);
}

.school-location {
  font-size: 0.875rem;
  color: var(--text-secondary);
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

.school-actions {
  display: flex;
  padding: 0 var(--space-4) var(--space-4);
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
}

/* 裁剪器弹窗 */
.cropper-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  z-index: 9999;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.cropper-container {
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.cropper-header {
  padding: var(--space-4);
  border-bottom: 1px solid var(--border-color-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cropper-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: var(--text-primary);
  font-weight: 600;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: var(--text-secondary);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.btn-close:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.cropper-body {
  height: 400px;
  overflow: hidden;
  background-color: var(--bg-tertiary);
  position: relative;
}

.cropper-controls {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: var(--space-2);
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-full);
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(8px);
}

.control-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--bg-primary);
  color: var(--text-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s;
}

.control-btn:hover {
  background: var(--bg-tertiary);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.cropper-instructions {
  position: absolute;
  bottom: 62px;
  left: 50%;
  transform: translateX(-50%);
  padding: var(--space-2) var(--space-4);
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  max-width: 90%;
  text-align: center;
  backdrop-filter: blur(8px);
  box-shadow: var(--shadow-sm);
}

.cropper-instructions p {
  margin: var(--space-1) 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.cropper-footer {
  padding: var(--space-4);
  border-top: 1px solid var(--border-color-light);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  min-height: 300px;
  color: var(--text-secondary);
}

.loading-container .loading-spinner {
  border-color: rgba(0, 0, 0, 0.1);
  border-top-color: var(--primary-600);
}

/* 响应式 */
@media (max-width: 768px) {
  .profile-tabs-bar {
    width: 100%;
  }

  .tab-btn {
    flex: 1;
    justify-content: center;
    padding: var(--space-2) var(--space-2);
    font-size: 0.875rem;
  }

  .panel-header {
    width: 100%;
  }

  .panel-actions {
    width: 100%;
  }

  .panel-actions .btn {
    flex: 1;
  }

  .activity-item {
    flex-direction: column;
  }

  .activity-time {
    margin-bottom: var(--space-2);
  }

  .school-grid,
  .friend-grid {
    grid-template-columns: 1fr;
  }

  input,
  textarea {
    font-size: 0.95rem;
  }

  .btn {
    padding: 0.625rem 1rem;
    font-size: 0.9rem;
  }

  .danger-zone .btn {
    width: 100%;
    margin-right: 0;
  }

  .profile-avatar {
    width: 100px;
    height: 100px;
  }

  .profile-name {
    font-size: 1.5rem;
  }

  .profile-bio {
    font-size: 0.9rem;
  }
}

@media (max-width: 480px) {
  .profile-banner {
    height: 180px;
  }

  .banner-change {
    opacity: 0.85;
    bottom: 8px;
    right: 8px;
    font-size: 0.75rem;
    padding: 6px 10px;
  }

  .profile-header-body {
    padding: 0 var(--space-4) var(--space-5);
  }

  .profile-avatar-wrapper {
    margin-top: -50px;
  }

  .profile-avatar {
    width: 90px;
    height: 90px;
  }

  .avatar-change {
    opacity: 0.85;
    font-size: 0.7rem;
  }

  .profile-name {
    font-size: 1.3rem;
    margin-top: 0.75rem;
  }

  .profile-bio {
    font-size: 0.85rem;
  }

  .form-group {
    margin-bottom: var(--space-4);
  }

  .search-wrapper {
    flex-direction: column;
  }

  .search-input {
    border-radius: var(--radius-md);
    border-right: 1px solid var(--border-color);
    margin-bottom: var(--space-2);
  }

  .search-btn {
    border-radius: var(--radius-md);
    width: 100%;
  }

  .user-item,
  .request-item {
    flex-wrap: wrap;
    gap: var(--space-2);
  }

  .request-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .friend-actions {
    flex-direction: column;
  }

  .school-actions {
    flex-direction: column;
    gap: var(--space-2);
  }

  .school-actions .btn {
    width: 100%;
  }

  .btn-icon {
    align-self: flex-end;
  }

  .cropper-body {
    height: 300px;
  }

  .cropper-instructions p {
    font-size: 0.75rem;
  }

  .cropper-footer button {
    padding: 8px 12px;
    font-size: 0.8rem;
  }

  .control-btn {
    width: 32px;
    height: 32px;
  }

  .cropper-controls {
    gap: var(--space-1);
    padding: var(--space-1) var(--space-2);
  }
}
</style>
