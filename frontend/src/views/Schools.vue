<template>
  <div class="schools-page container-wide page-padding">
    <SectionHeader
      title="院校库"
      subtitle="发现全国高校信息，对比专业与录取数据"
      icon="i-ep-school"
    />

    <GlassCard :hover="false" class="filter-card" padding="md">
      <div class="search-box">
        <div class="input-wrapper">
          <span class="i-ep-search search-icon" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索院校名称"
            @input="debounceSearch"
          />
        </div>

        <el-button
          v-if="isAdmin"
          type="primary"
          size="small"
          @click="showImportDialog = true"
          class="import-button"
        >
          导入学校数据
        </el-button>
      </div>

      <div class="filters">
        <div class="filter-group">
          <label>省份</label>
          <select v-model="selectedProvince" @change="handleSearch">
            <option value="">全部省份</option>
            <option v-for="province in provinces" :key="province" :value="province">
              {{ province }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>院校类型</label>
          <select v-model="selectedType" @change="handleSearch">
            <option value="">全部类型</option>
            <option v-for="(label, value) in schoolTypes" :key="value" :value="value">
              {{ label }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>办学层次</label>
          <select v-model="selectedLevel" @change="handleSearch">
            <option value="">全部层次</option>
            <option v-for="(label, value) in schoolLevels" :key="value" :value="value">
              {{ label }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>排序方式</label>
          <select v-model="sortBy" @change="handleSearch">
            <option value="ranking">按排名</option>
            <option value="name">按名称</option>
            <option value="founded_year">按建校时间</option>
          </select>
        </div>
      </div>
    </GlassCard>

    <div v-if="loading" class="loading-indicator">
      <el-skeleton :rows="6" animated />
      <span>加载中...</span>
    </div>

    <div v-else-if="error" class="error-state">
      <el-alert :title="error" type="error" show-icon @close="error = null" />
    </div>

    <div v-else-if="schools.length === 0" class="empty-state">
      <el-empty description="未找到符合条件的院校" :image-size="200">
        <template #extra>
          <el-button type="primary" @click="resetFilters">重置筛选条件</el-button>
        </template>
      </el-empty>
    </div>

    <div v-else class="schools-grid">
      <SchoolCard v-for="school in schools" :key="school.id" :school="school" />
    </div>

    <div v-if="schools.length > 0" class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="perPage"
        :total="totalItems"
        :page-sizes="[12, 24, 36, 48]"
        layout="total, sizes, prev, pager, next"
        @size-change="handlePageChange"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 导入学校CSV对话框 -->
    <el-dialog v-model="showImportDialog" title="导入学校数据" width="500px">
      <div class="import-dialog-content">
        <p class="import-tips">
          请上传包含学校数据的CSV文件，要求包含以下字段：name（学校名称）、province（省份）等
        </p>

        <el-upload
          class="upload-demo"
          drag
          action=""
          :auto-upload="false"
          :on-change="handleFileChange"
          :limit="1"
          accept=".csv"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            拖动文件到此处或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">仅支持CSV格式文件</div>
          </template>
        </el-upload>

        <div v-if="importResult" class="import-result">
          <p>导入结果：</p>
          <ul>
            <li>成功导入：{{ importResult.success_count }} 条</li>
            <li>导入失败：{{ importResult.error_count }} 条</li>
            <li>总记录数：{{ importResult.total }} 条</li>
          </ul>

          <div v-if="importResult.errors && importResult.errors.length > 0" class="import-errors">
            <p>部分错误信息：</p>
            <ul>
              <li v-for="(error, index) in importResult.errors" :key="index">{{ error }}</li>
            </ul>
          </div>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showImportDialog = false">取消</el-button>
          <el-button
            type="primary"
            :loading="importing"
            :disabled="!selectedFile"
            @click="handleImportSubmit"
          >
            开始导入
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { logger } from '@/utils/logger'
import { ref, computed, onMounted } from 'vue'
import { schoolApi } from '../api/school'
import type { School, SchoolQueryParams, ImportCsvResponse } from '../types/school'
import SchoolCard from '../components/SchoolCard.vue'
import GlassCard from '../components/GlassCard.vue'
import SectionHeader from '../components/SectionHeader.vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/userStore'

// 数据
const schools = ref<School[]>([])
const provinces = ref<string[]>([])
const schoolTypes = ref<{ [key: string]: string }>({})
const schoolLevels = ref<{ [key: string]: string }>({})
const loading = ref(true)
const error = ref<string | null>(null)

// 筛选和排序
const searchQuery = ref('')
const selectedProvince = ref('')
const selectedType = ref('')
const selectedLevel = ref('')
const sortBy = ref('ranking')

// 分页
const currentPage = ref(1)
const totalPages = ref(1)
const totalItems = ref(0)
const perPage = 12

// 获取学校数据
const fetchSchools = async () => {
  loading.value = true
  error.value = null
  try {
    const params: SchoolQueryParams = {
      page: currentPage.value,
      pageSize: perPage,
      search: searchQuery.value,
      province: selectedProvince.value,
      school_type: selectedType.value,
      school_level: selectedLevel.value,
      sort_by: sortBy.value
    }

    const response = await schoolApi.getSchools(params)
    if (response && 'results' in response && 'count' in response) {
      schools.value = response.results as School[]
      totalItems.value = response.count as number
      totalPages.value = Math.ceil((response.count as number) / perPage)
    } else {
      throw new Error('Invalid response format')
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '获取院校列表失败'
    ElMessage.error(error.value)
    schools.value = []
    totalItems.value = 0
    totalPages.value = 1
  } finally {
    loading.value = false
  }
}

// 获取筛选数据
const fetchFilterData = async () => {
  try {
    const [provincesRes, typesRes, levelsRes] = await Promise.all([
      schoolApi.getProvinces(),
      schoolApi.getSchoolTypes(),
      schoolApi.getSchoolLevels()
    ])

    if (Array.isArray(provincesRes)) {
      provinces.value = provincesRes
    }
    if (typesRes && typeof typesRes === 'object') {
      schoolTypes.value = typesRes as unknown as { [key: string]: string }
    }
    if (levelsRes && typeof levelsRes === 'object') {
      schoolLevels.value = levelsRes as unknown as { [key: string]: string }
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '获取筛选数据失败'
    ElMessage.error(error.value)
  }
}

// 搜索防抖
let searchTimeout: number | null = null
const debounceSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    handleSearch()
  }, 300) as unknown as number
}

const handleSearch = () => {
  currentPage.value = 1
  fetchSchools()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchSchools()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 重置筛选条件
const resetFilters = () => {
  searchQuery.value = ''
  selectedProvince.value = ''
  selectedType.value = ''
  selectedLevel.value = ''
  sortBy.value = 'ranking'
  currentPage.value = 1
  fetchSchools()
}

// 初始化
onMounted(async () => {
  logger.log('Schools组件已挂载，开始加载数据')
  try {
    await fetchFilterData()
    await fetchSchools()
  } catch (err) {
    console.error('初始化加载失败:', err)
    error.value = err instanceof Error ? err.message : '初始化加载失败'
    ElMessage.error(error.value)
  }
})

// 导入功能
const isAdmin = computed(() => {
  const userStore = useUserStore()
  return userStore.user?.is_staff === true || userStore.user?.is_superuser === true
})
const showImportDialog = ref(false)
const selectedFile = ref<File | null>(null)
const importResult = ref<ImportCsvResponse | null>(null)
const importing = ref(false)

// 处理文件选择
const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
}

// 处理导入提交
const handleImportSubmit = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择CSV文件')
    return
  }

  importing.value = true
  importResult.value = null

  try {
    const response = await schoolApi.importSchoolsCsv(selectedFile.value)
    importResult.value = response
    ElMessage.success(`成功导入${response.success_count}条学校数据`)

    if (response.success_count > 0) {
      await fetchSchools()
    }
  } catch (err) {
    console.error('导入学校数据失败:', err)
    ElMessage.error('导入学校数据失败')
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.schools-page {
  min-height: 100vh;
}

.filter-card {
  margin-bottom: var(--space-6);
}

.search-box {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
  position: relative;
}

.input-wrapper {
  position: relative;
  flex: 1;
  max-width: 420px;
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  color: var(--text-tertiary);
  pointer-events: none;
}

input {
  width: 100%;
  padding: 10px 14px 10px 40px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: 0.95rem;
  color: var(--text-primary);
  background: var(--bg-primary);
  transition: all 0.2s ease;
}

input:focus {
  outline: none;
  border-color: var(--primary-400);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--space-4);
}

.filter-group label {
  display: block;
  margin-bottom: var(--space-2);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
}

select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  color: var(--text-primary);
  background: var(--bg-primary);
  transition: all 0.2s ease;
  cursor: pointer;
}

select:focus {
  outline: none;
  border-color: var(--primary-400);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.loading-indicator {
  text-align: center;
  padding: var(--space-10);
  color: var(--text-secondary);
}

.loading-indicator span {
  display: block;
  margin-top: var(--space-4);
}

.error-state {
  margin: var(--space-4) 0;
}

.empty-state {
  padding: var(--space-10);
  text-align: center;
}

.schools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--space-5);
  margin-bottom: var(--space-6);
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: var(--space-6);
}

.import-button {
  flex-shrink: 0;
}

.import-dialog-content {
  text-align: center;
}

.import-tips {
  margin-bottom: var(--space-5);
  color: var(--text-secondary);
  line-height: 1.6;
}

.upload-demo {
  margin-bottom: var(--space-5);
}

.import-result {
  margin-bottom: var(--space-5);
  text-align: left;
  padding: var(--space-4);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.import-result ul {
  list-style: none;
  margin-top: var(--space-2);
}

.import-result li {
  padding: var(--space-1) 0;
  color: var(--text-secondary);
}

.import-errors {
  margin-top: var(--space-3);
  color: var(--error-color);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

@media (max-width: 640px) {
  .search-box {
    flex-wrap: wrap;
  }

  .input-wrapper {
    max-width: none;
    width: 100%;
  }

  .import-button {
    width: 100%;
  }

  .filters {
    grid-template-columns: 1fr;
  }
}
</style>
