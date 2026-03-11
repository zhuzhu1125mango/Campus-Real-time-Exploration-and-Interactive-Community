<template>
  <div class="profile-container">
    <div class="profile-header">
      <div class="profile-banner" :style="bannerStyle">
        <label for="banner-upload" class="banner-change">
          <input 
            id="banner-upload" 
            type="file" 
            accept="image/*"
            @change="handleBannerChange"
            hidden
          />
          <span class="upload-icon"></span>
          更换背景图
        </label>
      </div>
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
            <span class="upload-icon"></span>
            更换头像
          </label>
        </div>
      </div>
      <h1 class="profile-name">{{ form.username }}</h1>
      <p class="profile-bio">{{ form.bio || '这个人很懒，还没有填写个人简介' }}</p>
    </div>

    <div class="profile-tabs">
      <button 
        class="tab-button" 
        :class="{ active: activeTab === 'profile' }" 
        @click="activeTab = 'profile'"
      >
        个人资料
      </button>
      <button 
        class="tab-button" 
        :class="{ active: activeTab === 'activity' }" 
        @click="activeTab = 'activity'"
      >
        我的动态
      </button>
      <button 
        class="tab-button" 
        :class="{ active: activeTab === 'favorites' }" 
        @click="activeTab = 'favorites'"
      >
        收藏学校
      </button>
      <button 
        class="tab-button" 
        :class="{ active: activeTab === 'settings' }" 
        @click="activeTab = 'settings'"
      >
        账号设置
      </button>
    </div>

    <div class="profile-content">
      <div v-if="activeTab === 'profile'" class="profile-info-section">
        <div class="profile-card">
          <h2 class="section-title">个人资料</h2>
          <form @submit.prevent="handleUpdate" class="profile-form">
            <div class="form-group">
              <label for="username">用户名</label>
              <div class="input-wrapper">
                <span class="input-icon user-icon"></span>
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
                <span class="input-icon email-icon"></span>
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
                <span class="input-icon phone-icon"></span>
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
              <button type="submit" class="btn-save" :disabled="loading">
                <span v-if="loading" class="loading-spinner"></span>
                <span>{{ loading ? '保存中...' : '保存修改' }}</span>
              </button>
            </div>
          </form>
        </div>
      </div>

      <div v-if="activeTab === 'activity'" class="activity-section">
        <div class="profile-card">
          <h2 class="section-title">我的动态</h2>
          
          <div class="activity-list">
            <div class="empty-activity" v-if="activities.length === 0">
              <div class="empty-icon"></div>
              <p class="empty-text">您还没有发布任何动态</p>
              <div class="mt-4">
                <button class="btn-primary">发布第一条动态</button>
              </div>
            </div>
            
            <div v-else class="activity-items">
              <div class="activity-item" v-for="(activity, index) in activities" :key="index">
                <div class="activity-time">{{ activity.time }}</div>
                <div class="activity-content">
                  <div class="activity-type">{{ activity.type }}</div>
                  <p class="activity-text">{{ activity.content }}</p>
                  <div class="activity-footer">
                    <span class="activity-likes">{{ activity.likes }} 人点赞</span>
                    <span class="activity-comments">{{ activity.comments }} 条评论</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 新增收藏学校标签页 -->
      <div v-if="activeTab === 'favorites'" class="favorites-section">
        <div class="profile-card">
          <h2 class="section-title">收藏学校</h2>
          
          <div class="favorites-list">
            <div class="empty-favorites" v-if="favoriteSchools.length === 0">
              <div class="empty-icon school-icon"></div>
              <p class="empty-text">您还没有收藏任何学校</p>
              <div class="mt-4">
                <router-link to="/schools" class="btn-primary">前往浏览学校</router-link>
              </div>
            </div>
            
            <div v-else class="school-grid">
              <div class="school-card" v-for="school in favoriteSchools" :key="school.id">
                <div class="school-image" :style="{ backgroundImage: `url(${school.image || defaultSchoolImage})` }"></div>
                <div class="school-info">
                  <h3 class="school-name">{{ school.name }}</h3>
                  <p class="school-location">{{ school.location }}</p>
                </div>
                <div class="school-actions">
                  <router-link :to="`/schools/${school.id}`" class="btn-view">查看详情</router-link>
                  <button @click="removeFavorite(school.id)" class="btn-unfavorite">
                    <span class="unfavorite-icon"></span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'settings'" class="settings-section">
        <div class="profile-card">
          <h2 class="section-title">账号设置</h2>
          
          <div class="settings-group">
            <h3>密码修改</h3>
            <div class="form-group">
              <label for="old-password">当前密码</label>
              <div class="input-wrapper">
                <span class="input-icon password-icon"></span>
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
                  <span :class="['toggle-password-icon', showOldPassword ? 'show' : 'hide']"></span>
                </button>
              </div>
            </div>
            
            <div class="form-group">
              <label for="new-password">新密码</label>
              <div class="input-wrapper">
                <span class="input-icon password-icon"></span>
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
                  <span :class="['toggle-password-icon', showNewPassword ? 'show' : 'hide']"></span>
                </button>
              </div>
            </div>
            
            <div class="form-group">
              <label for="confirm-password">确认新密码</label>
              <div class="input-wrapper">
                <span class="input-icon password-icon"></span>
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
                  <span :class="['toggle-password-icon', showConfirmPassword ? 'show' : 'hide']"></span>
                </button>
              </div>
            </div>
            
            <div class="form-actions">
              <button @click="changePassword" class="btn-save" :disabled="pwdLoading">
                <span v-if="pwdLoading" class="loading-spinner"></span>
                <span>{{ pwdLoading ? '修改中...' : '修改密码' }}</span>
              </button>
            </div>
          </div>
          
          <div class="settings-group danger-zone">
            <h3>危险操作</h3>
            <button @click="logoutAllDevices" class="btn-warning">退出所有设备</button>
            <button @click="deactivateAccount" class="btn-danger">注销账号</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 图片裁剪弹窗 -->
    <div class="cropper-modal" v-if="showCropper">
      <div class="cropper-container">
        <div class="cropper-header">
          <h3>{{ cropperType === 'avatar' ? '裁剪头像 - 自由框选截取区域' : '裁剪背景图 - 自由框选截取区域' }}</h3>
          <button class="btn-close" @click="cancelCrop">×</button>
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
            <button class="control-btn" @click="zoomIn"><span class="zoom-in-icon"></span></button>
            <button class="control-btn" @click="zoomOut"><span class="zoom-out-icon"></span></button>
            <button class="control-btn" @click="rotateLeft"><span class="rotate-left-icon"></span></button>
            <button class="control-btn" @click="rotateRight"><span class="rotate-right-icon"></span></button>
            <button class="control-btn" @click="resetCropper"><span class="reset-icon"></span></button>
          </div>
          <div class="cropper-instructions">
            <p>您可以通过拖拽裁剪框四角或边缘调整大小，拖拽裁剪框内部移动位置</p>
            <p>使用上方按钮可放大、缩小、旋转图片或重置裁剪</p>
          </div>
        </div>
        <div class="cropper-footer">
          <button class="btn-secondary" @click="cancelCrop">取消</button>
          <button class="btn-primary" @click="confirmCrop">确认</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue'
import { userApi } from '../api/user'
import type { User } from '../types/user'
import { useToast } from '../composables/useToast'
// @ts-ignore 忽略类型检查错误
import VueCropper from 'vue-cropperjs'
// 使用本地CSS文件
import '../assets/cropper.css'
import { useUserStore } from '../stores/userStore'
import { ElMessage } from 'element-plus'

// 获取用户Store
const userStore = useUserStore()

// 基本数据
const loading = ref(false)
const pwdLoading = ref(false)
const isSubmitting = ref(false) // 添加提交状态变量
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

const favoriteSchools = ref<School[]>([])
const defaultSchoolImage = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M12 3L1 9l4 2.18v6L12 21l7-3.82v-6l2-1.09V17h2V9L12 3zm6.82 6L12 12.72 5.18 9 12 5.28 18.82 9zM17 15.99l-5 2.73-5-2.73v-3.72L12 15l5-2.73v3.72z"/></svg>'

// 模拟活动数据
const activities = ref([
  {
    type: '发布了帖子',
    content: '有谁知道如何解决Vue3中的类型问题？我遇到了一些困难...',
    time: '昨天 14:30',
    likes: 5,
    comments: 3
  },
  {
    type: '分享了资源',
    content: '整理了一份前端面试题集合，希望对准备实习的同学有所帮助！',
    time: '3天前',
    likes: 24,
    comments: 12
  },
  {
    type: '回复了问题',
    content: '这个问题我遇到过，可以通过调整webpack配置来解决...',
    time: '上周',
    likes: 8,
    comments: 1
  }
])

// 计算属性：头像样式
const avatarStyle = computed(() => {
  // 调试信息
  console.log('头像渲染：', {
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
      url = `${apiBaseUrl.value}${url.startsWith('/') ? '' : '/'}${url}`
    }
    
    // 添加时间戳防止缓存
    const timestamp = new Date().getTime()
    url = url.includes('?') ? `${url.split('?')[0]}?_=${timestamp}` : `${url}?_=${timestamp}`
    
    console.log('渲染头像绝对URL:', url)
    return { backgroundImage: `url(${url})` }
  }
  
  // 其次使用用户存储中的头像
  if (userStore.user?.avatar) {
    // 确保是绝对路径
    let url = userStore.user.avatar
    if (!url.startsWith('http') && !url.startsWith('data:')) {
      url = `${apiBaseUrl.value}${url.startsWith('/') ? '' : '/'}${url}`
    }
    
    // 添加时间戳防止缓存
    const timestamp = new Date().getTime()
    url = url.includes('?') ? `${url.split('?')[0]}?_=${timestamp}` : `${url}?_=${timestamp}`
    
    console.log('渲染用户存储头像绝对URL:', url)
    return { backgroundImage: `url(${url})` }
  }
  
  // 最后使用表单中的头像
  if (form.value.avatar && typeof form.value.avatar === 'string') {
    // 确保是绝对路径
    let url = form.value.avatar
    if (!url.startsWith('http') && !url.startsWith('data:')) {
      url = `${apiBaseUrl.value}${url.startsWith('/') ? '' : '/'}${url}`
    }
    
    // 添加时间戳防止缓存
    const timestamp = new Date().getTime()
    url = url.includes('?') ? `${url.split('?')[0]}?_=${timestamp}` : `${url}?_=${timestamp}`
    
    console.log('渲染表单头像绝对URL:', url)
    return { backgroundImage: `url(${url})` }
  }
  
  // 无头像时使用默认头像
  console.log('无头像，使用默认头像')
  return { backgroundImage: 'url(/imgs/default-avatar.png)' }
})

// 计算属性：背景图样式
const bannerStyle = computed(() => {
  // 调试信息
  console.log('背景图渲染：', {
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
      url = `${import.meta.env.VITE_API_BASE_URL}${url.startsWith('/') ? '' : '/'}${url}`
    }
    
    // 添加时间戳防止缓存
    const timestamp = new Date().getTime()
    url = url.includes('?') ? `${url.split('?')[0]}?_=${timestamp}` : `${url}?_=${timestamp}`
    
    console.log('渲染背景图绝对URL:', url)
    return { backgroundImage: `url(${url})` }
  }
  
  // 其次使用用户存储中的背景图
  if (userStore.user?.banner) {
    // 确保是绝对路径
    let url = userStore.user.banner
    if (!url.startsWith('http') && !url.startsWith('data:')) {
      url = `${import.meta.env.VITE_API_BASE_URL}${url.startsWith('/') ? '' : '/'}${url}`
    }
    
    // 添加时间戳防止缓存
    const timestamp = new Date().getTime()
    url = url.includes('?') ? `${url.split('?')[0]}?_=${timestamp}` : `${url}?_=${timestamp}`
    
    console.log('渲染用户存储背景图绝对URL:', url)
    return { backgroundImage: `url(${url})` }
  }
  
  // 最后使用表单中的背景图
  if (form.value.banner && typeof form.value.banner === 'string') {
    // 确保是绝对路径
    let url = form.value.banner
    if (!url.startsWith('http') && !url.startsWith('data:')) {
      url = `${import.meta.env.VITE_API_BASE_URL}${url.startsWith('/') ? '' : '/'}${url}`
    }
    
    // 添加时间戳防止缓存
    const timestamp = new Date().getTime()
    url = url.includes('?') ? `${url.split('?')[0]}?_=${timestamp}` : `${url}?_=${timestamp}`
    
    console.log('渲染表单背景图绝对URL:', url)
    return { backgroundImage: `url(${url})` }
  }
  
  // 无背景图时使用默认渐变色
  console.log('无背景图，使用默认渐变色')
  return { background: 'linear-gradient(135deg, #4361ee, #3a56d4)' }
})

// 获取用户资料
const fetchProfile = async () => {
  try {
    const response = await userApi.getProfile()
    console.log('获取到的用户资料:', response)
    
    // 只复制需要的字段，避免类型不匹配问题
    form.value = {
      username: response.username || '',
      email: response.email || '',
      phone: response.phone || '',
      bio: response.bio || '',
      avatar: null, // 不直接使用URL
      banner: null  // 不直接使用URL
    }
    
    // 设置用户头像预览 - 直接使用完整URL
    if (response.avatar && typeof response.avatar === 'string') {
      // 记录原始数据
      console.log('原始头像URL:', response.avatar)
      
      // 确保URL是完整的
      let avatarUrl = response.avatar
      if (!avatarUrl.startsWith('http') && !avatarUrl.startsWith('/')) {
        // 如果是相对路径，添加API基础URL
        const baseMediaUrl = import.meta.env.VITE_UPLOAD_URL || 'http://localhost:8000/media'
        avatarUrl = `${baseMediaUrl}/${avatarUrl}`
        console.log('添加基础URL后:', avatarUrl)
      }
      
      // 添加时间戳参数防止缓存
      const timestamp = new Date().getTime()
      const newAvatarUrl = avatarUrl.includes('?') 
        ? `${avatarUrl}&_=${timestamp}` 
        : `${avatarUrl}?_=${timestamp}`
      
      console.log('最终头像URL:', newAvatarUrl)
      avatarPreview.value = newAvatarUrl
    }
    
    // 设置用户背景图预览 - 直接使用完整URL
    if (response.banner && typeof response.banner === 'string') {
      console.log('服务器返回的背景图URL:', response.banner)
      
      // 处理Banner URL
      let bannerUrl = response.banner
      
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
      
      console.log('处理后的背景图URL:', finalBannerUrl)
    
      // 清除旧的Blob URL
      if (bannerPreview.value && bannerPreview.value.startsWith('blob:')) {
        URL.revokeObjectURL(bannerPreview.value)
      }
      
      // 立即更新背景图预览
      bannerPreview.value = finalBannerUrl
      console.log('更新背景图预览为最新URL:', bannerPreview.value)
    
      // 强制触发渲染
      setTimeout(() => {
        const tempUrl = bannerPreview.value
        bannerPreview.value = ''
        setTimeout(() => {
          bannerPreview.value = tempUrl
          console.log('刷新背景图预览完成')
        }, 50)
      }, 0)
    }
    
    // 刷新userStore中的数据
    if (!userStore.user || !userStore.user.avatar || !userStore.user.banner) {
      console.log('从profile更新userStore数据')
      await userStore.fetchUserProfile()
    }
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
  if (!file.type.includes('image/')) {
    showToast('请选择图片文件', 'error')
    input.value = '' // 清空input
    return
  }
  
  // 验证文件大小（2MB）
  if (file.size > 1024 * 1024 * 2) {
    showToast('图片大小不能超过2MB', 'error')
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
  if (!file.type.includes('image/')) {
    showToast('请选择图片文件', 'error')
    input.value = '' // 清空input
    return
  }
  
  // 验证文件大小（5MB）
  if (file.size > 1024 * 1024 * 5) {
    showToast('图片大小不能超过5MB', 'error')
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
    console.log('生成的DataURL开头部分:', dataUrl.substring(0, 50) + '...')
    
    // 转换为文件对象
    const blobBin = atob(dataUrl.split(',')[1])
    const array = []
    for (let i = 0; i < blobBin.length; i++) {
      array.push(blobBin.charCodeAt(i))
    }
    const blob = new Blob([new Uint8Array(array)], { type: 'image/jpeg' })
    console.log('生成的Blob对象:', blob.type, blob.size, '字节')
    
    // 获取原始文件名作为参考
    let fileName = ''
    if (cropperType.value === 'avatar') {
      fileName = `avatar_${Date.now()}.jpg`
    } else {
      fileName = `banner_${Date.now()}.jpg`
    }
    
    // 创建File对象
    const newFile = new File([blob], fileName, { type: 'image/jpeg', lastModified: Date.now() })
    console.log('创建文件成功:', fileName, newFile.size, '字节')
    
    // 将文件对象保存到表单
    if (cropperType.value === 'avatar') {
      form.value.avatar = newFile
      avatarPreview.value = dataUrl
      console.log('设置头像预览:', {
        预览URL类型: typeof avatarPreview.value,
        开头: avatarPreview.value.substring(0, 30) + '...',
        form中的文件: form.value.avatar ? `是(${form.value.avatar.name})` : '否'
      })
    } else {
      form.value.banner = newFile
      bannerPreview.value = dataUrl
      console.log('设置背景图预览:', {
        预览URL类型: typeof bannerPreview.value,
        开头: bannerPreview.value.substring(0, 30) + '...',
        form中的文件: form.value.banner ? `是(${form.value.banner.name})` : '否'
      })
    }
    
    // 关闭裁剪界面
    showCropper.value = false
    
    // 自动保存更改
    console.log('准备保存修改后的图片...')
    await handleUpdate()
    showToast('图片裁剪并保存成功', 'success')
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
    console.log('开始更新用户资料...', form.value);
    
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
      console.log('处理头像...');
      // 如果是文件对象，直接添加
      if (form.value.avatar instanceof File) {
        console.log('头像是File对象');
        formData.append('avatar', form.value.avatar);
      }
      // 如果是Data URL，转换为文件
      else if (typeof form.value.avatar === 'string' && form.value.avatar.startsWith('data:')) {
        console.log('头像是Data URL');
        const avatarFile = dataURLtoFile(form.value.avatar, `avatar_${Date.now()}.jpg`);
        formData.append('avatar', avatarFile);
      }
      // 如果是已有的URL
      else if (typeof form.value.avatar === 'string' && !form.value.avatar.startsWith('blob:')) {
        // 如果URL没有改变，不需要重新上传
        if (form.value.avatar === userStore.user?.avatar) {
          console.log('头像URL未变更，不需要重新上传');
        } else {
          console.log('头像是URL，需要重新上传');
          formData.append('avatar', form.value.avatar);
        }
      }
    }
    
    // 单独处理背景图片文件
    if (form.value.banner) {
      console.log('处理背景图...');
      // 如果是文件对象，直接添加
      if (form.value.banner instanceof File) {
        console.log('背景图是File对象');
        formData.append('banner', form.value.banner);
      }
      // 如果是Data URL，转换为文件
      else if (typeof form.value.banner === 'string' && form.value.banner.startsWith('data:')) {
        console.log('背景图是Data URL');
        const bannerFile = dataURLtoFile(form.value.banner, `banner_${Date.now()}.jpg`);
        formData.append('banner', bannerFile);
      }
      // 如果是已有的URL
      else if (typeof form.value.banner === 'string' && !form.value.banner.startsWith('blob:')) {
        // 如果URL没有改变，不需要重新上传
        if (form.value.banner === userStore.user?.banner) {
          console.log('背景图URL未变更，不需要重新上传');
        } else {
          console.log('背景图是URL，需要重新上传');
          formData.append('banner', form.value.banner);
        }
      }
    }
    
    // 打印FormData内容供调试
    for (const pair of formData.entries()) {
      console.log(`FormData: ${pair[0]}: ${pair[1]}`);
    }
    
    // 发送更新请求
    const response = await userApi.updateProfile(formData);
    
    // 重新获取最新的用户数据
    await userStore.fetchUserProfile();
    
    // 清除本地预览数据
    avatarPreview.value = '';
    bannerPreview.value = '';
    
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
  } catch (error: any) {
    console.error('密码修改失败:', error)
    let errorMsg = '密码修改失败，请检查当前密码是否正确'
    if (error.response?.data?.detail) {
      errorMsg = error.response.data.detail
    }
    showToast(errorMsg, 'error')
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
      if (favorite.content_type && favorite.content_type.includes('school') && favorite.object_id) {
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
  
  // 页面加载时恢复之前的预览
  if (localStorage.getItem('tempAvatarPreview')) {
    avatarPreview.value = localStorage.getItem('tempAvatarPreview') || ''
  }
  if (localStorage.getItem('tempBannerPreview')) {
    bannerPreview.value = localStorage.getItem('tempBannerPreview') || ''
  }
  
  // 添加调试状态
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

// 添加调试状态
const debugInfo = ref<string | null>(null);

// 测试图片URL
const testImageUrls = async () => {
  debugInfo.value = '正在测试图片URL...';
  
  try {
    // 测试用户头像URL
    const avatarUrl = userStore.user?.avatar;
    
    // 组装不同形式的URL进行测试
    const urls = [];
    
    if (avatarUrl) {
      // 原始URL
      urls.push({ name: '原始URL', url: avatarUrl });
      
      // 绝对URL
      if (!avatarUrl.startsWith('http')) {
        const absoluteUrl = `${import.meta.env.VITE_API_BASE_URL}${avatarUrl.startsWith('/') ? '' : '/'}${avatarUrl}`;
        urls.push({ name: '绝对URL', url: absoluteUrl });
      }
      
      // 带时间戳的URL
      const timestamp = new Date().getTime();
      const timestampUrl = avatarUrl.includes('?') 
        ? `${avatarUrl.split('?')[0]}?_=${timestamp}` 
        : `${avatarUrl}?_=${timestamp}`;
      urls.push({ name: '带时间戳URL', url: timestampUrl });
    }
    
    // 测试每个URL
    const results = await Promise.all(
      urls.map(async ({ name, url }) => {
        try {
          const response = await fetch(url, { method: 'HEAD' });
          return { 
            name, 
            url, 
            status: response.status,
            ok: response.ok,
            statusText: response.statusText
          };
        } catch (error: any) {
          return { name, url, error: error.message };
        }
      })
    );
    
    debugInfo.value = JSON.stringify(results, null, 2);
  } catch (error: any) {
    debugInfo.value = `测试出错: ${error.message}`;
    console.error('测试图片URL出错:', error);
  }
};

// 检查静态文件
const checkStaticFiles = async () => {
  debugInfo.value = '正在检查静态文件...';
  
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/users/test-static/`);
    const data = await response.json();
    debugInfo.value = JSON.stringify(data, null, 2);
    
    // 测试图片直接访问
    if (data.test_image_url) {
      const imgUrl = data.test_image_url.startsWith('/')
        ? `${import.meta.env.VITE_API_BASE_URL}${data.test_image_url}`
        : `${import.meta.env.VITE_API_BASE_URL}/${data.test_image_url}`;
        
      try {
        const imgResponse = await fetch(imgUrl, { method: 'HEAD' });
        debugInfo.value += `\n\n测试图片访问结果:\nURL: ${imgUrl}\n状态: ${imgResponse.status}\n成功: ${imgResponse.ok}`;
      } catch (imgError: any) {
        debugInfo.value += `\n\n测试图片访问出错:\nURL: ${imgUrl}\n错误: ${imgError.message}`;
      }
    }
  } catch (error: any) {
    debugInfo.value = `检查静态文件出错: ${error.message}`;
    console.error('检查静态文件出错:', error);
  }
};

// 列出所有头像文件
const listAvatarFiles = async () => {
  debugInfo.value = '正在获取所有头像文件...';
  
  try {
    const response = await fetch(`${apiBaseUrl.value}/api/users/list-avatars/`);
    const data = await response.json();
    debugInfo.value = JSON.stringify(data, null, 2);
  } catch (error: any) {
    debugInfo.value = `获取头像文件列表出错: ${error.message}`;
    console.error('获取头像文件列表出错:', error);
  }
};

// 打开媒体测试页面
const openMediaTestPage = () => {
  // 添加可选的测试页面选项
  debugInfo.value = '选择要打开的测试页面:';
  
  const djangoTestPage = `${import.meta.env.VITE_API_BASE_URL}/test-media/`;
  const htmlTestPage = `${import.meta.env.VITE_API_BASE_URL}/api/users/test-html-media/`;
  
  // 创建按钮并添加到调试信息面板
  const testPageButtons = `
    <div style="margin-top: 10px;">
      <button onclick="window.open('${djangoTestPage}', '_blank')" style="margin-right: 10px; padding: 5px 10px;">
        打开Django模板测试页面
      </button>
      
      <button onclick="window.open('${htmlTestPage}', '_blank')" style="padding: 5px 10px;">
        打开HTML API测试页面
      </button>
    </div>
  `;
  
  debugInfo.value += testPageButtons;
};

// 添加是否为开发环境的计算属性
const isDevelopment = ref(import.meta.env.DEV);

// 获取API基础URL
const apiBaseUrl = ref(import.meta.env.VITE_API_BASE_URL || '');
</script>

<style scoped>
.profile-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.mt-4 {
  margin-top: 1.5rem;
}

.profile-header {
  position: relative;
  border-radius: 16px;
  background-color: white;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
  text-align: center;
  overflow: hidden;
  margin-bottom: 2rem;
}

.profile-banner {
  height: 260px;
  background: linear-gradient(135deg, #4361ee, #3a56d4);
  background-size: cover;
  background-position: center;
  position: relative;
  width: 100%;
}

.banner-change {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background-color: rgba(0, 0, 0, 0.6);
  color: white;
  border-radius: 4px;
  text-align: center;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
  opacity: 0.9;
  transition: opacity 0.3s;
  display: flex;
  align-items: center;
  gap: 4px;
  z-index: 10;
}

.profile-banner:hover .banner-change {
  opacity: 1;
}

.banner-change:hover, .banner-change:focus {
  opacity: 1 !important;
}

/* 在小屏幕上保持背景更换按钮可见 */
@media (max-width: 480px) {
  .profile-banner {
    height: 200px;
  }
  
  .profile-avatar-wrapper {
    top: 150px;
  }
  
  .profile-name {
    margin-top: 40px;
  }

  .banner-change {
    opacity: 0.8;
  }
}

.profile-avatar-wrapper {
  position: absolute;
  top: 180px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  z-index: 5;
}

.profile-avatar {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background-color: #4361ee;
  border: 4px solid white;
  position: relative;
  background-size: cover;
  background-position: center;
  overflow: hidden;
}

.avatar-change {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: rgba(0, 0, 0, 0.4);
  color: white;
  text-align: center;
  padding: 4px 0;
  font-size: 12px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.3s;
  z-index: 10;
}

.profile-avatar:hover .avatar-change {
  opacity: 1;
}

.avatar-change:hover, .avatar-change:focus {
  opacity: 1 !important;
}

.upload-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white"><path d="M5 10h4v6h6v-6h4l-7-7-7 7zm0 8v2h14v-2H5z"/></svg>');
  width: 16px;
  height: 16px;
  display: inline-block;
  vertical-align: middle;
}

.profile-name {
  font-size: 1.8rem;
  font-weight: 700;
  margin: 70px 0 0.5rem;
  color: #333;
}

.profile-bio {
  color: #666;
  max-width: 600px;
  margin: 0 auto 2rem;
  padding: 0 1rem;
}

.profile-tabs {
  display: flex;
  background-color: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
  margin-bottom: 2rem;
}

.tab-button {
  flex: 1;
  padding: 1.2rem 1rem;
  background: none;
  border: none;
  font-size: 1rem;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
}

.tab-button:hover {
  background-color: #f9fafc;
}

.tab-button.active {
  color: #4361ee;
  font-weight: 600;
  box-shadow: inset 0 -2px 0 #4361ee;
}

.profile-content {
  margin-bottom: 2rem;
}

.profile-card {
  background-color: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
}

.section-title {
  font-size: 1.5rem;
  color: #333;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f0f0f0;
}

/* 表单样式 */
.profile-form {
  max-width: 600px;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: #555;
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
  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;
  opacity: 0.5;
}

.user-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>');
}

.email-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>');
}

.phone-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>');
}

.password-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/></svg>');
}

input, textarea {
  width: 100%;
  padding: 0.8rem 0.8rem 0.8rem 2.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s;
}

.bio-textarea {
  padding: 0.8rem;
  resize: vertical;
}

input:focus, textarea:focus {
  outline: none;
  border-color: #4361ee;
  box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.1);
}

.form-actions {
  margin-top: 2rem;
}

.btn-save {
  padding: 0.9rem 2rem;
  background-color: #4361ee;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
}

.btn-save:hover {
  background-color: #3a56d4;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(67, 97, 238, 0.2);
}

.btn-save:disabled {
  background-color: #b0b0b0;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 活动记录样式 */
.activity-list {
  min-height: 300px;
}

.empty-activity {
  text-align: center;
  padding: 3rem 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.empty-icon {
  width: 100px;
  height: 100px;
  margin: 0 auto 1.5rem;
  opacity: 0.3;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>');
  background-repeat: no-repeat;
  background-position: center;
}

.empty-text {
  margin: 0;
  max-width: 80%;
  text-align: center;
  color: #666;
}

.btn-primary {
  padding: 0.8rem 1.5rem;
  background-color: #4361ee;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-block;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.btn-primary:hover {
  background-color: #3a56d4;
}

.btn-primary:active {
  transform: scale(0.98);
  background-color: #3550c8;
}

.activity-item {
  display: flex;
  padding: 1.2rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.activity-item:last-child {
  border: none;
}

.activity-time {
  min-width: 100px;
  color: #888;
  padding-top: 0.2rem;
}

.activity-content {
  flex: 1;
}

.activity-type {
  font-weight: 600;
  color: #4361ee;
  margin-bottom: 0.5rem;
}

.activity-text {
  margin-bottom: 0.8rem;
  color: #444;
}

.activity-footer {
  display: flex;
  gap: 1rem;
  color: #888;
  font-size: 0.9rem;
}

/* 账号设置样式 */
.settings-group {
  margin-bottom: 2.5rem;
}

.settings-group h3 {
  font-size: 1.2rem;
  color: #444;
  margin-bottom: 1.5rem;
}

.danger-zone {
  border-top: 1px solid #f0f0f0;
  padding-top: 2rem;
}

.btn-warning {
  padding: 0.8rem 1.5rem;
  background-color: #ff9800;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  margin-right: 1rem;
  transition: all 0.3s;
}

.btn-warning:hover {
  background-color: #f57c00;
}

.btn-danger {
  padding: 0.8rem 1.5rem;
  background-color: #f44336;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-danger:hover {
  background-color: #d32f2f;
}

/* 收藏学校样式 */
.school-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 1rem;
}

.school-card {
  background-color: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  transition: all 0.3s;
  border: 1px solid #f0f0f0;
}

.school-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.school-image {
  height: 140px;
  background-color: #f5f6fa;
  background-size: cover;
  background-position: center;
}

.school-info {
  padding: 15px;
}

.school-name {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 5px;
  color: #333;
}

.school-location {
  font-size: 0.9rem;
  color: #666;
}

.school-actions {
  display: flex;
  padding: 10px 15px 15px;
  justify-content: space-between;
  align-items: center;
}

.btn-view {
  padding: 8px 15px;
  background-color: #4361ee;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.3s;
}

.btn-view:hover {
  background-color: #3a56d4;
}

.btn-unfavorite {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: none;
  background-color: #f0f0f0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.btn-unfavorite:hover {
  background-color: #ff4d4f;
}

.unfavorite-icon {
  width: 20px;
  height: 20px;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23666"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>');
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
}

.btn-unfavorite:hover .unfavorite-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>');
}

.empty-favorites {
  text-align: center;
  padding: 3rem 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.school-icon {
  width: 100px;
  height: 100px;
  margin: 0 auto;
  opacity: 0.3;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M12 3L1 9l4 2.18v6L12 21l7-3.82v-6l2-1.09V17h2V9L12 3zm6.82 6L12 12.72 5.18 9 12 5.28 18.82 9zM17 15.99l-5 2.73-5-2.73v-3.72L12 15l5-2.73v3.72z"/></svg>');
  background-repeat: no-repeat;
  background-position: center;
}

/* 响应式样式 */
@media (max-width: 768px) {
  .profile-tabs {
    flex-direction: column;
  }
  
  .tab-button {
    padding: 1rem 0.5rem;
    font-size: 0.9rem;
  }
  
  .activity-item {
    flex-direction: column;
  }
  
  .activity-time {
    margin-bottom: 0.5rem;
  }
  
  .school-grid {
    grid-template-columns: 1fr;
  }
  
  .profile-card {
    padding: 1.5rem 1rem;
  }
  
  .section-title {
    font-size: 1.3rem;
  }
  
  .btn-save, .btn-primary, .btn-warning, .btn-danger {
    width: 100%;
    margin-bottom: 0.5rem;
  }
  
  .settings-group {
    margin-bottom: 2rem;
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
  
  .empty-favorites p, .empty-activity p {
    padding: 0 1rem;
  }
}

@media (max-width: 480px) {
  .profile-banner {
    height: 150px;
  }
  
  .banner-change {
    opacity: 0.8;
    bottom: 5px;
    right: 5px;
    font-size: 10px;
    padding: 4px 8px;
  }
  
  .profile-avatar-wrapper {
    margin-top: -50px;
  }
  
  .profile-avatar {
    width: 80px;
    height: 80px;
  }
  
  .avatar-change {
    opacity: 0.8;
    font-size: 10px;
  }
  
  .profile-name {
    font-size: 1.3rem;
    margin-top: 0.7rem;
  }
  
  .profile-bio {
    font-size: 0.8rem;
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  input, textarea {
    font-size: 0.9rem;
    padding: 0.7rem 0.7rem 0.7rem 2.3rem;
  }
  
  .school-image {
    height: 120px;
  }
  
  .school-actions {
    flex-direction: column;
    gap: 10px;
  }
  
  .btn-view {
    width: 100%;
    text-align: center;
  }
  
  .btn-unfavorite {
    align-self: flex-end;
  }
  
  .empty-icon, .school-icon {
    width: 80px;
    height: 80px;
  }
}

/* 裁剪器样式 */
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
  background-color: white;
  border-radius: 12px;
  overflow: hidden;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.cropper-header {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cropper-header h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #333;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.btn-close:hover {
  background-color: #f5f5f5;
  color: #333;
}

.cropper-body {
  height: 400px;
  overflow: hidden;
  background-color: #f5f5f5;
  position: relative;
}

.cropper-controls {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 10px;
  background-color: rgba(255, 255, 255, 0.8);
  padding: 5px 10px;
  border-radius: 20px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.control-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background-color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
}

.control-btn:hover {
  background-color: #f0f0f0;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.zoom-in-icon, .zoom-out-icon, .rotate-left-icon, .rotate-right-icon, .reset-icon {
  width: 18px;
  height: 18px;
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
}

.zoom-in-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>');
}

.zoom-out-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M19 13H5v-2h14v2z"/></svg>');
}

.rotate-left-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M7.11 8.53L5.7 7.11C4.8 8.27 4.24 9.61 4.07 11h2.02c.14-.87.49-1.72 1.02-2.47zM6.09 13H4.07c.17 1.39.72 2.73 1.62 3.89l1.41-1.42c-.52-.75-.87-1.59-1.01-2.47zm1.01 5.32c1.16.9 2.51 1.44 3.9 1.61V17.9c-.87-.15-1.71-.49-2.46-1.03L7.1 18.32zM13 4.07V1L8.45 5.55 13 10V6.09c2.84.48 5 2.94 5 5.91s-2.16 5.43-5 5.91v2.02c3.95-.49 7-3.85 7-7.93s-3.05-7.44-7-7.93z"/></svg>');
}

.rotate-right-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M15.55 5.55L11 1v3.07C7.06 4.56 4 7.92 4 12s3.05 7.44 7 7.93v-2.02c-2.84-.48-5-2.94-5-5.91s2.16-5.43 5-5.91V10l4.55-4.45zM19.93 11c-.17-1.39-.72-2.73-1.62-3.89l-1.42 1.42c.54.75.88 1.6 1.02 2.47h2.02zM13 17.9v2.02c1.39-.17 2.74-.71 3.9-1.61l-1.44-1.44c-.75.54-1.59.89-2.46 1.03zm3.89-2.42l1.42 1.41c.9-1.16 1.45-2.5 1.62-3.89h-2.02c-.14.87-.48 1.72-1.02 2.48z"/></svg>');
}

.reset-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>');
}

.cropper-footer {
  padding: 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-secondary {
  padding: 8px 16px;
  background-color: #f5f5f5;
  color: #333;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-secondary:hover {
  background-color: #e9e9e9;
}

.cropper-instructions {
  padding: 10px;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 8px;
  margin: 10px auto;
  max-width: 90%;
  text-align: center;
}

.cropper-instructions p {
  margin: 5px 0;
  font-size: 0.9rem;
  color: #333;
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
  color: #666;
  outline: none;
}

.toggle-password-icon {
  width: 20px;
  height: 20px;
  display: inline-block;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}

.toggle-password-icon.show {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23666"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>');
}

.toggle-password-icon.hide {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23666"><path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/></svg>');
}

@media (max-width: 480px) {
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
  
  .zoom-in-icon, .zoom-out-icon, .rotate-left-icon, .rotate-right-icon, .reset-icon {
    width: 16px;
    height: 16px;
  }
  
  .cropper-controls {
    gap: 5px;
    padding: 4px 8px;
  }
}

.debug-panel {
  margin-top: 30px;
  padding: 15px;
  border: 1px dashed #ccc;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.debug-info {
  margin-top: 15px;
  padding: 10px;
  background-color: #eee;
  border-radius: 4px;
  font-family: monospace;
  white-space: pre-wrap;
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}
</style> 