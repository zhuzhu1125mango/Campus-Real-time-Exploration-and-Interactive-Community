<template>
  <div class="recommendation-section">
    <div class="recommendation-header">
      <h2>{{ title }}</h2>
      <div class="recommendation-tabs">
        <el-button 
          v-for="tab in tabs" 
          :key="tab.value"
          :type="activeTab === tab.value ? 'primary' : 'default'"
          @click="switchTab(tab.value)"
        >
          {{ tab.label }}
        </el-button>
      </div>
    </div>
    
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>
    
    <div v-else-if="error" class="error-container">
      <el-alert
        :title="error"
        type="error"
        show-icon
        :closable="false"
      />
      <el-button type="primary" @click="fetchRecommendations">重新加载</el-button>
    </div>
    
    <div v-else-if="recommendations.length === 0" class="empty-container">
      <el-empty description="暂无推荐内容" />
    </div>
    
    <div v-else class="recommendation-content">
      <div v-if="reasoning.length > 0" class="reasoning-section">
        <el-tag v-for="(reason, index) in reasoning" :key="index" size="small" effect="plain">
          {{ reason }}
        </el-tag>
      </div>
      
      <div class="recommendation-list" v-if="activeTab === 'schools'">
        <el-row :gutter="20">
          <el-col v-for="school in recommendations" :key="school.id" :xs="24" :sm="12" :md="8" :lg="6">
            <el-card class="recommendation-card" @click="goToSchoolDetail(school.id)">
              <template #header>
                <div class="school-header">
                  <h3>{{ school.name }}</h3>
                  <el-tag size="small">{{ school.school_type }}</el-tag>
                </div>
              </template>
              <div class="school-info">
                <p><el-icon><Location /></el-icon> {{ school.province }} {{ school.city }}</p>
                <p><el-icon><SchoolIcon /></el-icon> {{ school.school_level }}</p>
                <p v-if="school.national_rank"><el-icon><Top /></el-icon> 全国排名: {{ school.national_rank }}</p>
                <p v-if="school.average_rating"><el-icon><Star /></el-icon> 评分: {{ school.average_rating }}</p>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
      
      <div class="recommendation-list" v-else-if="activeTab === 'majors'">
        <el-row :gutter="20">
          <el-col v-for="major in recommendations" :key="major.id" :xs="24" :sm="12" :md="8" :lg="6">
            <el-card class="recommendation-card" @click="goToMajorDetail(major.id)">
              <template #header>
                <div class="major-header">
                  <h3>{{ major.name }}</h3>
                  <el-tag size="small">{{ major.degree_type }}</el-tag>
                </div>
              </template>
              <div class="major-info">
                <p><el-icon><InfoFilled /></el-icon> {{ major.code }}</p>
                <p><el-icon><Collection /></el-icon> {{ major.subject_category }}</p>
                <p v-if="major.employment_rate"><el-icon><Suitcase /></el-icon> 就业率: {{ major.employment_rate }}%</p>
                <p v-if="major.avg_salary"><el-icon><Money /></el-icon> 平均薪资: {{ major.avg_salary }}元</p>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
      
      <div class="recommendation-list" v-else-if="activeTab === 'posts'">
        <el-card v-for="post in recommendations" :key="post.id" class="post-card" @click="goToPostDetail(post.id)">
          <template #header>
            <div class="post-header">
              <h3>{{ post.title }}</h3>
              <el-tag size="small" v-if="post.tags && post.tags.length > 0">{{ post.tags[0] }}</el-tag>
            </div>
          </template>
          <div class="post-info">
            <p class="post-content">{{ truncateContent(post.content, 100) }}</p>
            <div class="post-meta">
              <span><el-icon><User /></el-icon> {{ post.author.username }}</span>
              <span><el-icon><ChatLineSquare /></el-icon> {{ post.comments_count }} 评论</span>
              <span><el-icon><Star /></el-icon> {{ post.likes_count }} 点赞</span>
              <span><el-icon><View /></el-icon> {{ post.views }} 浏览</span>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Location, School as SchoolIcon, Top, Star, InfoFilled, Collection, Suitcase, Money, User, ChatLineSquare, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { schoolApi } from '@/api/school'

interface RecommendationTab {
  label: string
  value: string
}

const props = defineProps({
  title: {
    type: String,
    default: '为你推荐'
  },
  limit: {
    type: Number,
    default: 6
  }
})

const router = useRouter()
const activeTab = ref('schools')
const recommendations = ref<any[]>([])
const reasoning = ref<string[]>([])
const loading = ref(false)
const error = ref('')

const tabs: RecommendationTab[] = [
  { label: '学校', value: 'schools' },
  { label: '专业', value: 'majors' },
  { label: '帖子', value: 'posts' }
]

const fetchRecommendations = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await schoolApi.getRecommendations({
      type: activeTab.value,
      limit: props.limit
    })
    
    if (response && 'recommendations' in response) {
      recommendations.value = response.recommendations || []
      reasoning.value = response.reasoning || []
    }
  } catch (err) {
    error.value = '获取推荐失败，请稍后重试'
    ElMessage.error('获取推荐失败')
  } finally {
    loading.value = false
  }
}

const switchTab = (tab: string) => {
  activeTab.value = tab
  fetchRecommendations()
}

const goToSchoolDetail = (schoolId: number) => {
  router.push(`/schools/${schoolId}`)
}

const goToMajorDetail = (majorId: number) => {
  // 假设专业详情页路由为 /majors/:id
  router.push(`/majors/${majorId}`)
}

const goToPostDetail = (postId: number) => {
  // 假设帖子详情页路由为 /forum/posts/:id
  router.push(`/forum/posts/${postId}`)
}

const truncateContent = (content: string, maxLength: number) => {
  if (content.length <= maxLength) {
    return content
  }
  return content.substring(0, maxLength) + '...'
}

onMounted(() => {
  fetchRecommendations()
})
</script>

<style scoped>
.recommendation-section {
  margin: 20px 0;
}

.recommendation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.recommendation-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.recommendation-tabs {
  display: flex;
  gap: 8px;
}

.loading-container {
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.error-container {
  padding: 20px;
  background-color: #fef0f0;
  border-radius: 8px;
  text-align: center;
}

.error-container .el-button {
  margin-top: 10px;
}

.empty-container {
  padding: 40px 0;
  text-align: center;
}

.reasoning-section {
  margin-bottom: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.recommendation-list {
  margin-top: 20px;
}

.recommendation-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.recommendation-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 2px 12px 0 rgba(0,0,0,.1);
}

.school-header,
.major-header,
.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.school-header h3,
.major-header h3,
.post-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.school-info,
.major-info {
  font-size: 14px;
  color: #666;
}

.school-info p,
.major-info p {
  margin: 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.post-card {
  margin-bottom: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.post-card:hover {
  box-shadow: 0 2px 12px 0 rgba(0,0,0,.1);
}

.post-content {
  margin: 12px 0;
  line-height: 1.5;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.post-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #999;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.post-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
