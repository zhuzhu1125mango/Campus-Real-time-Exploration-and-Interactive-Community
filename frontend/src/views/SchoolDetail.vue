<template>
  <div class="school-detail-page container-wide page-padding">
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>正在加载学校信息...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <div class="error-icon"><span class="i-ep-warning" /></div>
      <h3>加载失败</h3>
      <p>{{ error }}</p>
      <button class="retry-btn" @click="fetchSchoolDetail">重试</button>
    </div>

    <template v-else-if="school">
      <GlassCard :hover="false" class="school-header-card">
        <div class="school-header">
          <img :src="school.logo || '/default-school-logo.png'" :alt="school.name" class="school-logo" />
          <div class="school-title">
            <h1>{{ school.name }}</h1>
            <div class="school-tags">
              <span class="school-badge" :class="getBadgeClass(school.school_level)">
                {{ school.school_level }}
              </span>
              <span class="school-location">{{ school.province }}</span>
              <span class="school-type">{{ school.school_type }}</span>
            </div>
          </div>
          <button
            class="favorite-btn"
            :class="{ 'is-favorite': isFavorite, loading: favoriteLoading }"
            :disabled="favoriteLoading"
            @click="toggleFavorite"
          >
            <span class="favorite-icon">{{ isFavorite ? '♥' : '♡' }}</span>
            <span class="favorite-text">{{ isFavorite ? '已收藏' : '收藏院校' }}</span>
          </button>
        </div>
      </GlassCard>

      <GlassCard :hover="false" class="tab-card" padding="none">
        <div class="tabs">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            class="tab-btn"
            :class="{ active: activeTab === tab.id }"
            @click="activeTab = tab.id"
          >
            {{ tab.name }}
          </button>

          <router-link
            v-if="school"
            class="forum-link"
            :to="school.board_id ? `/forum/board/${school.board_id}` : `/forum/${Number(school.id)}`"
          >
            进入学校论坛
          </router-link>
        </div>

        <div v-if="activeTab === 'overview'" class="tab-content">
          <div class="section">
            <h2>学校简介</h2>
            <p class="intro-text">{{ school.introduction }}</p>
          </div>

          <div class="section">
            <h2>基本信息</h2>
            <div class="info-grid">
              <GlassCard
                v-for="item in infoItems"
                :key="item.label"
                :hover="false"
                padding="sm"
                class="info-card"
              >
                <span class="label">{{ item.label }}</span>
                <span class="value">{{ item.value }}</span>
              </GlassCard>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'majors'" class="tab-content">
          <div class="section">
            <h2>专业设置</h2>
            <div class="search-majors">
              <span class="i-ep-search major-search-icon" />
              <input
                v-model="majorSearch"
                type="text"
                placeholder="搜索专业..."
                class="search-input"
              />
            </div>

            <div v-if="filteredMajors.length === 0" class="empty-state">
              <p>未找到相关专业</p>
            </div>

            <div v-else class="majors-grid">
              <GlassCard v-for="major in filteredMajors" :key="major.id" :hover="true" class="major-card">
                <h3>{{ major.name }}</h3>
                <p>{{ major.description }}</p>
                <div class="major-stats">
                  <span>就业率: {{ major.employment_rate }}%</span>
                  <span>平均薪资: {{ major.avg_salary }}元/月</span>
                </div>
              </GlassCard>
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

            <GlassCard v-if="isLoggedIn" :hover="false" class="rating-form-card">
              <h3>分享你的评价</h3>
              <div class="rating-stars">
                <button
                  v-for="star in 5"
                  :key="star"
                  class="star-btn"
                  :class="{ active: userRating >= star }"
                  @click="userRating = star"
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

              <button class="submit-rating" @click="submitRating">提交评价</button>
            </GlassCard>

            <GlassCard v-else :hover="false" class="login-notice">
              <p>请登录后进行评价</p>
              <router-link to="/login" class="login-btn">去登录</router-link>
            </GlassCard>

            <div class="ratings-list">
              <h3>用户评价 ({{ ratings.length }})</h3>

              <div v-if="ratings.length === 0" class="empty-ratings">
                <p>暂无评价</p>
              </div>

              <div v-else class="rating-items">
                <GlassCard v-for="(rating, index) in ratings" :key="index" :hover="true" class="rating-item">
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
                </GlassCard>
              </div>

              <div v-if="totalRatingPages > 1" class="pagination">
                <button class="page-btn" :disabled="ratingPage === 1" @click="ratingPage--">上一页</button>
                <span>{{ ratingPage }} / {{ totalRatingPages }}</span>
                <button class="page-btn" :disabled="ratingPage === totalRatingPages" @click="ratingPage++">
                  下一页
                </button>
              </div>
            </div>
          </div>
        </div>
      </GlassCard>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { schoolApi } from '../api/school'
import type { School, SchoolRating } from '../types/school'
import { useUserStore } from '../stores/userStore'
import { ElMessage } from 'element-plus'
import { getErrorMessage, getApiErrorMessage } from '../utils/error'
import GlassCard from '../components/GlassCard.vue'

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
const isFavorite = ref(false)
const favoriteLoading = ref(false)

// 计算属性
const isLoggedIn = computed(() => userStore.isLoggedIn)

// 选项卡
const tabs = [
  { id: 'overview', name: '学校概况' },
  { id: 'majors', name: '专业设置' },
  { id: 'scores', name: '分数线' },
  { id: 'ratings', name: '用户评价' }
]

const infoItems = computed(() => {
  if (!school.value) return []
  return [
    { label: '综合排名', value: school.value.national_rank || '暂无' },
    { label: '录取率', value: school.value.admission_rate ? school.value.admission_rate + '%' : '暂无' },
    { label: '办学层次', value: school.value.school_level || '暂无' },
    { label: '建校时间', value: school.value.founded_year || '暂无' }
  ]
})

// 筛选专业
const filteredMajors = computed(() => {
  if (!school.value || !school.value.majors) return []

  if (!majorSearch.value) return school.value.majors

  return school.value.majors.filter((major) =>
    major.name.toLowerCase().includes(majorSearch.value.toLowerCase())
  )
})

// 分数线筛选
const filteredScores = computed(() => {
  if (!school.value || !school.value.admission_scores) return []

  return school.value.admission_scores.filter((score) => {
    if (selectedProvince.value && score.province !== selectedProvince.value) return false
    if (selectedYear.value && score.year !== parseInt(selectedYear.value)) return false
    return true
  })
})

// 省份列表
const provinces = computed(() => {
  if (!school.value || !school.value.admission_scores) return []

  const set = new Set<string>()
  school.value.admission_scores.forEach((score) => {
    if (score.province) set.add(score.province)
  })

  return Array.from(set)
})

// 年份列表
const years = computed(() => {
  if (!school.value || !school.value.admission_scores) return []

  const set = new Set<number>()
  school.value.admission_scores.forEach((score) => {
    set.add(score.year)
  })

  return Array.from(set).sort((a, b) => b - a)
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
    school.value = response
    isFavorite.value = response.is_favorited || false
  } catch (err) {
    error.value = getErrorMessage(err, '获取学校信息失败，请稍后重试')
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

    ratings.value = response.results
    totalRatingPages.value = Math.ceil(response.count / 10)
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
      rating: userRating.value,
      comment: userComment.value.trim()
    })

    userRating.value = 0
    userComment.value = ''
    ratingPage.value = 1
    fetchSchoolRatings()
  } catch (err) {
    console.error('提交评价失败:', err)
  }
}

// 切换收藏状态
const toggleFavorite = async () => {
  if (!school.value || !isLoggedIn.value) {
    if (!isLoggedIn.value) {
      ElMessage.warning('请先登录')
      router.push('/login')
    }
    return
  }

  if (favoriteLoading.value) return

  favoriteLoading.value = true
  try {
    if (isFavorite.value) {
      await schoolApi.unfavoriteSchool(school.value.id)
      isFavorite.value = false
      ElMessage.success('已取消收藏')
    } else {
      await schoolApi.favoriteSchool(school.value.id)
      isFavorite.value = true
      ElMessage.success('收藏成功')
    }
  } catch (err) {
    ElMessage.error(getApiErrorMessage(err, '操作失败'))
  } finally {
    favoriteLoading.value = false
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
.school-detail-page {
  min-height: 100vh;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-12) 0;
  text-align: center;
  color: var(--text-secondary);
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid var(--primary-200);
  border-radius: 50%;
  border-top-color: var(--primary-600);
  animation: spin 1s linear infinite;
  margin-bottom: var(--space-4);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-icon {
  width: 60px;
  height: 60px;
  font-size: 2.5rem;
  color: var(--error-color);
  margin-bottom: var(--space-4);
}

.error-state h3 {
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}

.retry-btn {
  margin-top: var(--space-4);
  padding: 0.6rem 1.5rem;
  background-color: var(--primary-600);
  color: var(--text-inverse);
  border: none;
  border-radius: var(--radius-md);
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
}

.retry-btn:hover {
  background-color: var(--primary-700);
}

.school-header-card {
  margin-bottom: var(--space-6);
}

.school-header {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}

.school-logo {
  width: 140px;
  height: 140px;
  object-fit: cover;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
}

.school-title {
  flex: 1;
}

.school-title h1 {
  margin: 0 0 var(--space-3) 0;
  color: var(--text-primary);
  font-size: 2rem;
  font-weight: 700;
}

.school-tags {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.school-badge {
  padding: 0.35rem 0.8rem;
  border-radius: var(--radius-full);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-inverse);
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

.school-location,
.school-type {
  padding: 0.35rem 0.8rem;
  background: var(--bg-tertiary);
  border-radius: var(--radius-full);
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.tab-card {
  overflow: hidden;
}

.tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color-light);
  background: var(--bg-tertiary);
  padding: 0 var(--space-4);
}

.tab-btn {
  padding: var(--space-4) var(--space-5);
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-secondary);
  transition: all 0.25s ease;
  position: relative;
}

.tab-btn:hover {
  color: var(--primary-600);
}

.tab-btn.active {
  color: var(--primary-600);
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background-color: var(--primary-600);
  border-radius: 3px 3px 0 0;
}

.dark .tab-btn:hover,
.dark .tab-btn.active {
  color: var(--primary-400);
}

.dark .tab-btn.active::after {
  background-color: var(--primary-400);
}

.tab-content {
  padding: var(--space-6);
}

.section {
  margin-bottom: var(--space-8);
}

.section:last-child {
  margin-bottom: 0;
}

.section h2 {
  margin: 0 0 var(--space-4) 0;
  color: var(--text-primary);
  font-size: 1.25rem;
  font-weight: 700;
}

.intro-text {
  color: var(--text-secondary);
  line-height: 1.8;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-4);
}

.info-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.info-card .label {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.info-card .value {
  color: var(--text-primary);
  font-size: 1.4rem;
  font-weight: 700;
}

.search-majors {
  position: relative;
  margin-bottom: var(--space-5);
  max-width: 420px;
}

.major-search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  color: var(--text-tertiary);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 10px 14px 10px 40px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: 0.95rem;
  color: var(--text-primary);
  background: var(--bg-primary);
  transition: all 0.2s ease;
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-400);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.empty-state {
  text-align: center;
  padding: var(--space-8) 0;
  color: var(--text-secondary);
}

.majors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

.major-card h3 {
  margin: 0 0 var(--space-2) 0;
  color: var(--text-primary);
  font-size: 1.1rem;
}

.major-card p {
  margin: 0 0 var(--space-3) 0;
  color: var(--text-secondary);
  line-height: 1.5;
  font-size: 0.9rem;
}

.major-stats {
  display: flex;
  justify-content: space-between;
  color: var(--text-tertiary);
  font-size: 0.85rem;
  border-top: 1px solid var(--border-color-light);
  padding-top: var(--space-3);
}

.filter-row {
  display: flex;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

.filter-item {
  flex: 1;
  min-width: 180px;
}

.filter-item label {
  display: block;
  margin-bottom: var(--space-2);
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
}

.filter-item select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  color: var(--text-primary);
  background: var(--bg-primary);
  transition: all 0.2s ease;
}

.filter-item select:focus {
  outline: none;
  border-color: var(--primary-400);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.score-table {
  overflow-x: auto;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color-light);
}

.score-table table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: var(--space-3) var(--space-4);
  text-align: left;
  border-bottom: 1px solid var(--border-color-light);
}

th {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
  font-weight: 600;
}

tr:last-child td {
  border-bottom: none;
}

.rating-form-card {
  margin-bottom: var(--space-6);
}

.rating-form-card h3 {
  margin: 0 0 var(--space-3) 0;
  color: var(--text-primary);
  font-size: 1.1rem;
}

.rating-stars {
  display: flex;
  align-items: center;
  margin-bottom: var(--space-3);
}

.star-btn {
  background: none;
  border: none;
  font-size: 1.6rem;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: color 0.2s;
}

.star-btn.active {
  color: #ffc107;
}

.rating-text {
  margin-left: var(--space-3);
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.comment-input {
  width: 100%;
  height: 100px;
  padding: var(--space-3);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  color: var(--text-primary);
  background: var(--bg-primary);
  margin-bottom: var(--space-3);
  resize: vertical;
  transition: all 0.2s ease;
}

.comment-input:focus {
  outline: none;
  border-color: var(--primary-400);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.submit-rating {
  padding: 0.7rem 1.5rem;
  background-color: var(--primary-600);
  color: var(--text-inverse);
  border: none;
  border-radius: var(--radius-md);
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
}

.submit-rating:hover {
  background-color: var(--primary-700);
}

.login-notice {
  text-align: center;
  padding: var(--space-8) var(--space-4);
  margin-bottom: var(--space-6);
}

.login-notice p {
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
}

.login-btn {
  display: inline-block;
  padding: 0.6rem 1.5rem;
  background-color: var(--primary-600);
  color: var(--text-inverse);
  border-radius: var(--radius-md);
  font-weight: 600;
  transition: background-color 0.3s;
}

.login-btn:hover {
  background-color: var(--primary-700);
}

.ratings-list h3 {
  margin: 0 0 var(--space-4) 0;
  color: var(--text-primary);
  font-size: 1.1rem;
  font-weight: 700;
}

.empty-ratings {
  text-align: center;
  padding: var(--space-8) 0;
  color: var(--text-secondary);
}

.rating-items {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.rating-header {
  display: flex;
  align-items: center;
  margin-bottom: var(--space-3);
}

.user-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: var(--primary-600);
  color: var(--text-inverse);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  margin-right: var(--space-3);
  flex-shrink: 0;
}

.rating-info {
  flex: 1;
}

.rating-user {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.rating-stars-display span {
  color: var(--text-tertiary);
  font-size: 1.1rem;
}

.rating-stars-display span.filled {
  color: #ffc107;
}

.rating-date {
  color: var(--text-tertiary);
  font-size: 0.85rem;
}

.rating-comment {
  color: var(--text-secondary);
  line-height: 1.6;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-3);
  margin-top: var(--space-6);
}

.page-btn {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  border-color: var(--primary-400);
  color: var(--primary-600);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.forum-link {
  margin-left: auto;
  align-self: center;
  padding: 0.5rem 1rem;
  background: var(--primary-600);
  color: var(--text-inverse);
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: 0.9rem;
  transition: background-color 0.3s;
  text-decoration: none;
}

.forum-link:hover {
  background: var(--primary-700);
}

.favorite-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 0.7rem 1.4rem;
  background: var(--bg-primary);
  color: var(--primary-600);
  border: 1.5px solid var(--primary-600);
  border-radius: var(--radius-md);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  margin-left: auto;
  align-self: center;
}

.favorite-btn:hover:not(:disabled) {
  background: var(--primary-600);
  color: var(--text-inverse);
}

.favorite-btn.is-favorite {
  background: var(--primary-600);
  color: var(--text-inverse);
}

.favorite-btn.is-favorite:hover:not(:disabled) {
  background: var(--error-color);
  border-color: var(--error-color);
}

.favorite-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.favorite-icon {
  font-size: 1.1rem;
}

@media (max-width: 768px) {
  .school-header {
    flex-direction: column;
    text-align: center;
    gap: var(--space-4);
  }

  .school-logo {
    width: 120px;
    height: 120px;
  }

  .school-title h1 {
    font-size: 1.6rem;
  }

  .school-tags {
    justify-content: center;
  }

  .favorite-btn {
    margin-left: 0;
    align-self: stretch;
    justify-content: center;
  }

  .tabs {
    overflow-x: auto;
    white-space: nowrap;
    padding: 0;
  }

  .tab-btn {
    padding: var(--space-3) var(--space-4);
  }

  .forum-link {
    display: none;
  }

  .tab-content {
    padding: var(--space-4);
  }

  .info-grid,
  .majors-grid {
    grid-template-columns: 1fr;
  }

  .filter-row {
    flex-direction: column;
    gap: var(--space-3);
  }
}
</style>
