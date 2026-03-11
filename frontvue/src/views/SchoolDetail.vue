<template>
  <div class="school-detail-container">
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>正在加载学校信息...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <div class="error-icon"></div>
      <h3>加载失败</h3>
      <p>{{ error }}</p>
      <button @click="fetchSchoolDetail" class="retry-btn">重试</button>
    </div>

    <div v-else-if="school" class="school-content">
      <div class="school-header">
        <img :src="school.logo || '/default-school-logo.png'" :alt="school.name" class="school-logo" />
        <div class="school-title">
          <h1>{{ school.name }}</h1>
          <div class="school-tags">
            <span class="school-badge" :class="getBadgeClass(school.school_level)">{{ school.school_level }}</span>
            <span class="school-location">{{ school.province }}</span>
            <span class="school-type">{{ school.school_type }}</span>
          </div>
        </div>
      </div>

      <div class="tab-container">
        <div class="tabs">
          <button 
            v-for="tab in tabs" 
            :key="tab.id" 
            :class="{ active: activeTab === tab.id }"
            @click="activeTab = tab.id"
            class="tab-btn"
          >
            {{ tab.name }}
          </button>
          
          <router-link 
            v-if="school" 
            :to="`/forum/${Number(school.id)}`" 
            class="forum-link"
          >
            进入学校论坛
          </router-link>
        </div>

        <div v-if="activeTab === 'overview'" class="tab-content">
          <div class="section">
            <h2>学校简介</h2>
            <p>{{ school.introduction }}</p>
          </div>

          <div class="section">
            <h2>基本信息</h2>
            <div class="info-grid">
              <div class="info-item">
                <span class="label">综合排名</span>
                <span class="value">{{ school.national_rank || '暂无' }}</span>
              </div>
              <div class="info-item">
                <span class="label">录取率</span>
                <span class="value">{{ school.admission_rate ? school.admission_rate + '%' : '暂无' }}</span>
              </div>
              <div class="info-item">
                <span class="label">办学层次</span>
                <span class="value">{{ school.school_level || '暂无' }}</span>
              </div>
              <div class="info-item">
                <span class="label">建校时间</span>
                <span class="value">{{ school.founded_year || '暂无' }}</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'majors'" class="tab-content">
          <div class="section">
            <h2>专业设置</h2>
            <div class="search-majors">
              <input 
                type="text" 
                v-model="majorSearch" 
                placeholder="搜索专业..." 
                class="search-input"
              />
            </div>
            
            <div v-if="filteredMajors.length === 0" class="empty-state">
              <p>未找到相关专业</p>
            </div>
            
            <div v-else class="majors-grid">
              <div v-for="major in filteredMajors" :key="major.id" class="major-card">
                <h3>{{ major.name }}</h3>
                <p>{{ major.description }}</p>
                <div class="major-stats">
                  <span>就业率: {{ major.employment_rate }}%</span>
                  <span>平均薪资: {{ major.avg_salary }}元/月</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'scores'" class="tab-content">
          <div class="section">
            <h2>历年分数线</h2>
            
            <div class="filter-row">
              <div class="filter-item">
                <label>省份</label>
                <select v-model="selectedProvince">
                  <option value="">全部省份</option>
                  <option v-for="province in provinces" :key="province" :value="province">
                    {{ province }}
                  </option>
                </select>
              </div>
              
              <div class="filter-item">
                <label>年份</label>
                <select v-model="selectedYear">
                  <option value="">全部年份</option>
                  <option v-for="year in years" :key="year" :value="year">
                    {{ year }}
                  </option>
                </select>
              </div>
            </div>
            
            <div class="score-table">
              <table>
                <thead>
                  <tr>
                    <th>年份</th>
                    <th>省份</th>
                    <th>理科</th>
                    <th>文科</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="score in filteredScores" :key="`${score.year}-${score.province}`">
                    <td>{{ score.year }}</td>
                    <td>{{ score.province }}</td>
                    <td>{{ score.science || '-' }}</td>
                    <td>{{ score.arts || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'ratings'" class="tab-content">
          <div class="section">
            <h2>用户评价</h2>
            
            <div class="rating-form" v-if="isLoggedIn">
              <h3>分享你的评价</h3>
              <div class="rating-stars">
                <button 
                  v-for="star in 5" 
                  :key="star"
                  @click="userRating = star"
                  :class="{ active: userRating >= star }"
                  class="star-btn"
                >
                  ★
                </button>
                <span class="rating-text">{{ userRating }} 星</span>
              </div>
              
              <textarea 
                v-model="userComment" 
                placeholder="分享你对这所学校的看法..." 
                class="comment-input"
              ></textarea>
              
              <button @click="submitRating" class="submit-rating">提交评价</button>
            </div>
            
            <div v-else class="login-notice">
              <p>请登录后进行评价</p>
              <router-link to="/login" class="login-btn">去登录</router-link>
            </div>
            
            <div class="ratings-list">
              <h3>用户评价 ({{ ratings.length }})</h3>
              
              <div v-if="ratings.length === 0" class="empty-ratings">
                <p>暂无评价</p>
              </div>
              
              <div v-else class="rating-items">
                <div v-for="(rating, index) in ratings" :key="index" class="rating-item">
                  <div class="rating-header">
                    <div class="user-avatar">{{ rating.user.username.charAt(0) }}</div>
                    <div class="rating-info">
                      <div class="rating-user">{{ rating.user.username }}</div>
                      <div class="rating-stars-display">
                        <span v-for="star in 5" :key="star" :class="{ filled: rating.rating >= star }">★</span>
                      </div>
                    </div>
                    <div class="rating-date">{{ formatDate(rating.created_at) }}</div>
                  </div>
                  <div class="rating-comment">{{ rating.comment }}</div>
                </div>
              </div>
              
              <div class="pagination" v-if="totalRatingPages > 1">
                <button 
                  :disabled="ratingPage === 1"
                  @click="ratingPage--"
                  class="page-btn"
                >
                  上一页
                </button>
                <span>{{ ratingPage }} / {{ totalRatingPages }}</span>
                <button 
                  :disabled="ratingPage === totalRatingPages"
                  @click="ratingPage++"
                  class="page-btn"
                >
                  下一页
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { schoolApi } from '../api/school'
import type { School, AdmissionScore, Major, SchoolRating } from '../types/school'
import { useUserStore } from '../stores/userStore'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 状态
const school = ref<School | null>(null)
const loading = ref(true)
const error = ref('')
const activeTab = ref('overview')
const majorSearch = ref('')
const selectedProvince = ref('')
const selectedYear = ref('')
const userRating = ref(0)
const userComment = ref('')
const ratings = ref<SchoolRating[]>([])
const ratingPage = ref(1)
const totalRatingPages = ref(1)

// 计算属性
const isLoggedIn = computed(() => userStore.isLoggedIn)

// 选项卡
const tabs = [
  { id: 'overview', name: '学校概况' },
  { id: 'majors', name: '专业设置' },
  { id: 'scores', name: '分数线' },
  { id: 'ratings', name: '用户评价' }
]

// 筛选专业
const filteredMajors = computed(() => {
  if (!school.value || !school.value.majors) return []
  
  if (!majorSearch.value) return school.value.majors
  
  return school.value.majors.filter(major => 
    major.name.toLowerCase().includes(majorSearch.value.toLowerCase())
  )
})

// 分数线筛选
const filteredScores = computed(() => {
  if (!school.value || !school.value.admission_scores) return []
  
  return school.value.admission_scores.filter(score => {
    if (selectedProvince.value && score.province !== selectedProvince.value) return false
    if (selectedYear.value && score.year !== parseInt(selectedYear.value)) return false
    return true
  })
})

// 省份列表
const provinces = computed(() => {
  if (!school.value || !school.value.admission_scores) return []
  
  const provinces = new Set<string>()
  school.value.admission_scores.forEach(score => {
    if (score.province) provinces.add(score.province)
  })
  
  return Array.from(provinces)
})

// 年份列表
const years = computed(() => {
  if (!school.value || !school.value.admission_scores) return []
  
  const years = new Set<number>()
  school.value.admission_scores.forEach(score => {
    years.add(score.year)
  })
  
  return Array.from(years).sort((a, b) => b - a) // 降序排列
})

// 根据学校层次获取徽章样式
const getBadgeClass = (level: string | undefined) => {
  if (!level) return 'badge-normal'
  
  switch (level) {
    case '985工程':
      return 'badge-985'
    case '211工程':
      return 'badge-211'
    case '双一流':
      return 'badge-double'
    default:
      return 'badge-normal'
  }
}

// 格式化日期
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

// 获取学校详情
const fetchSchoolDetail = async () => {
  const id = route.params.id
  if (!id) {
    router.push('/schools')
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    const response = await schoolApi.getSchool(Number(id))
    school.value = response.data
  } catch (err: any) {
    error.value = err.message || '获取学校信息失败，请稍后重试'
    console.error('获取学校详情失败:', err)
  } finally {
    loading.value = false
  }
}

// 获取学校评价
const fetchSchoolRatings = async () => {
  if (!school.value) return
  
  try {
    const response = await schoolApi.getSchoolRatings(school.value.id, {
      page: ratingPage.value
    })
    
    ratings.value = response.data.results
    totalRatingPages.value = Math.ceil(response.data.count / 10)
  } catch (err) {
    console.error('获取学校评价失败:', err)
  }
}

// 提交评价
const submitRating = async () => {
  if (!school.value || !userRating.value || !userComment.value.trim()) {
    return
  }
  
  try {
    await schoolApi.rateSchool(school.value.id, {
      score: userRating.value,
      comment: userComment.value.trim()
    })
    
    // 重置表单并刷新评价列表
    userRating.value = 0
    userComment.value = ''
    ratingPage.value = 1
    fetchSchoolRatings()
  } catch (err) {
    console.error('提交评价失败:', err)
  }
}

// 监听标签页变化
watch(activeTab, (newTab) => {
  if (newTab === 'ratings') {
    fetchSchoolRatings()
  }
})

// 监听评价页码变化
watch(ratingPage, () => {
  fetchSchoolRatings()
})

onMounted(() => {
  fetchSchoolDetail()
})
</script>

<style scoped>
.school-detail-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 0;
  text-align: center;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(67, 97, 238, 0.2);
  border-radius: 50%;
  border-top-color: #4361ee;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  width: 60px;
  height: 60px;
  margin-bottom: 1rem;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23e94560"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 11c-.55 0-1-.45-1-1V8c0-.55.45-1 1-1s1 .45 1 1v4c0 .55-.45 1-1 1zm1 4h-2v-2h2v2z"/></svg>');
  background-repeat: no-repeat;
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.6rem 1.5rem;
  background-color: #4361ee;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.retry-btn:hover {
  background-color: #3a56d4;
}

.school-header {
  display: flex;
  align-items: center;
  gap: 2rem;
  margin-bottom: 2rem;
  padding: 2rem;
  background-color: white;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
}

.school-logo {
  width: 160px;
  height: 160px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #eee;
}

.school-title h1 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 2.2rem;
}

.school-tags {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.school-badge {
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  color: white;
}

.badge-985 {
  background-color: #e91e63;
}

.badge-211 {
  background-color: #9c27b0;
}

.badge-double {
  background-color: #3f51b5;
}

.badge-normal {
  background-color: #607d8b;
}

.school-location, .school-type {
  padding: 0.4rem 0.8rem;
  background-color: #f5f5f5;
  border-radius: 20px;
  font-size: 0.9rem;
  color: #666;
}

.tab-container {
  background-color: white;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.tabs {
  display: flex;
  border-bottom: 1px solid #eee;
}

.tab-btn {
  padding: 1.2rem 2rem;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  color: #666;
  transition: all 0.3s;
  position: relative;
}

.tab-btn:hover {
  color: #4361ee;
}

.tab-btn.active {
  color: #4361ee;
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background-color: #4361ee;
}

.tab-content {
  padding: 2rem;
}

.section {
  margin-bottom: 2rem;
}

.section:last-child {
  margin-bottom: 0;
}

.section h2 {
  margin: 0 0 1.5rem 0;
  color: #333;
  font-size: 1.5rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
}

.info-item {
  padding: 1.5rem;
  background-color: #f8f9fa;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
}

.label {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.value {
  color: #333;
  font-size: 1.4rem;
  font-weight: 600;
}

.search-majors {
  margin-bottom: 1.5rem;
}

.search-input {
  width: 100%;
  padding: 0.8rem 1rem;
  border: 1px solid #eee;
  border-radius: 8px;
  font-size: 1rem;
}

.empty-state {
  text-align: center;
  padding: 2rem 0;
  color: #666;
}

.majors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.major-card {
  padding: 1.5rem;
  background-color: #f8f9fa;
  border-radius: 12px;
  transition: all 0.3s;
}

.major-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
}

.major-card h3 {
  margin: 0 0 0.8rem 0;
  color: #333;
}

.major-card p {
  margin: 0 0 1rem 0;
  color: #666;
  line-height: 1.5;
}

.major-stats {
  display: flex;
  justify-content: space-between;
  color: #888;
  font-size: 0.9rem;
  border-top: 1px solid #e0e0e0;
  padding-top: 0.8rem;
}

.filter-row {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.filter-item {
  flex: 1;
  min-width: 200px;
}

.filter-item label {
  display: block;
  margin-bottom: 0.5rem;
  color: #666;
  font-size: 0.9rem;
}

.filter-item select {
  width: 100%;
  padding: 0.8rem;
  border: 1px solid #eee;
  border-radius: 8px;
  font-size: 0.95rem;
}

.score-table {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #eee;
}

th {
  background-color: #f8f9fa;
  color: #333;
  font-weight: 600;
}

.rating-form {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background-color: #f8f9fa;
  border-radius: 12px;
}

.rating-form h3 {
  margin: 0 0 1rem 0;
  color: #333;
}

.rating-stars {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
}

.star-btn {
  background: none;
  border: none;
  font-size: 1.8rem;
  color: #ccc;
  cursor: pointer;
  transition: color 0.2s;
}

.star-btn.active {
  color: #ffc107;
}

.rating-text {
  margin-left: 1rem;
  color: #666;
}

.comment-input {
  width: 100%;
  height: 100px;
  padding: 0.8rem;
  border: 1px solid #eee;
  border-radius: 8px;
  font-size: 1rem;
  margin-bottom: 1rem;
  resize: vertical;
}

.submit-rating {
  padding: 0.8rem 1.5rem;
  background-color: #4361ee;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.submit-rating:hover {
  background-color: #3a56d4;
}

.login-notice {
  text-align: center;
  padding: 2rem;
  background-color: #f8f9fa;
  border-radius: 12px;
  margin-bottom: 2rem;
}

.login-btn {
  display: inline-block;
  margin-top: 0.5rem;
  padding: 0.6rem 1.5rem;
  background-color: #4361ee;
  color: white;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s;
}

.login-btn:hover {
  background-color: #3a56d4;
}

.ratings-list h3 {
  margin: 0 0 1.5rem 0;
  color: #333;
}

.empty-ratings {
  text-align: center;
  padding: 2rem 0;
  color: #666;
}

.rating-items {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.rating-item {
  padding: 1.5rem;
  background-color: #f8f9fa;
  border-radius: 12px;
}

.rating-header {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #4361ee;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  margin-right: 1rem;
}

.rating-info {
  flex: 1;
}

.rating-user {
  font-weight: 600;
  color: #333;
  margin-bottom: 0.2rem;
}

.rating-stars-display span {
  color: #ccc;
  font-size: 1.2rem;
}

.rating-stars-display span.filled {
  color: #ffc107;
}

.rating-date {
  color: #999;
  font-size: 0.9rem;
}

.rating-comment {
  color: #555;
  line-height: 1.5;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}

.page-btn {
  padding: 0.6rem 1rem;
  border: 1px solid #eee;
  border-radius: 8px;
  background-color: white;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
}

.page-btn:hover:not(:disabled) {
  border-color: #4361ee;
  color: #4361ee;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.forum-link {
  padding: 1.2rem 2rem;
  background-color: #4361ee;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  text-decoration: none;
  margin-left: auto;
}

.forum-link:hover {
  background-color: #3a56d4;
}

@media (max-width: 768px) {
  .school-header {
    flex-direction: column;
    padding: 1.5rem;
    gap: 1rem;
    text-align: center;
  }
  
  .school-logo {
    width: 120px;
    height: 120px;
  }
  
  .school-title h1 {
    font-size: 1.8rem;
  }
  
  .school-tags {
    justify-content: center;
  }
  
  .tabs {
    overflow-x: auto;
    white-space: nowrap;
  }
  
  .tab-btn {
    padding: 1rem;
  }
  
  .tab-content {
    padding: 1.5rem;
  }
  
  .info-grid, .majors-grid {
    grid-template-columns: 1fr;
  }
  
  .filter-row {
    flex-direction: column;
    gap: 1rem;
  }
}
</style> 