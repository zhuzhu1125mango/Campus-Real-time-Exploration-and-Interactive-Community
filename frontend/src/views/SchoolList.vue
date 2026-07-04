<template>
  <div class="school-list">
    <h2>学校列表</h2>
    
    <!-- 搜索和筛选 -->
    <div class="filters">
      <TheSearch
        v-model="searchQuery"
        placeholder="搜索学校名称"
        class="search-input"
        @search="handleSearch"
        @clear="handleSearch"
      />
      
      <el-select v-model="selectedProvince" placeholder="选择省份" @change="handleProvinceChange">
        <el-option
          v-for="province in provinces"
          :key="province"
          :label="province"
          :value="province"
        />
      </el-select>
      
      <el-select v-model="selectedCity" placeholder="选择城市" @change="handleSearch">
        <el-option
          v-for="city in cities"
          :key="city"
          :label="city"
          :value="city"
        />
      </el-select>
    </div>

    <!-- 学校列表 -->
    <el-row :gutter="20">
      <el-col v-for="school in schools" :key="school.id" :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="school-card" @click="goToSchoolDetail(school.id)">
          <template #header>
            <div class="school-header">
              <h3>{{ school.name }}</h3>
              <el-tag size="small">{{ school.school_type }}</el-tag>
            </div>
          </template>
          <div class="school-info">
            <p><el-icon><Location /></el-icon> {{ school.province }} {{ school.city }}</p>
            <p><el-icon><SchoolIcon /></el-icon> {{ school.school_level }}</p>
            <p><el-icon><InfoFilled /></el-icon> {{ school.introduction || '暂无描述' }}</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[12, 24, 36, 48]"
        layout="total, sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Location, School as SchoolIcon, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { schoolApi } from '@/api/school'
import type { School } from '@/types/school'
import TheSearch from '@/components/common/TheSearch.vue'

const router = useRouter()
const schools = ref<School[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(12)
const searchQuery = ref('')
const selectedProvince = ref('')
const selectedCity = ref('')
const provinces = ref<string[]>([])
const cities = ref<string[]>([])

// 获取学校列表
const fetchSchools = async () => {
  try {
    const response = await schoolApi.getSchools({
      page: currentPage.value,
      pageSize: pageSize.value,
      search: searchQuery.value,
      province: selectedProvince.value,
      city: selectedCity.value
    })
    if (response && 'results' in response && 'count' in response) {
      schools.value = response.results as School[]
      total.value = response.count as number
    }
  } catch (error) {
    ElMessage.error('获取学校列表失败')
  }
}

// 获取省份列表
const fetchProvinces = async () => {
  try {
    const response = await schoolApi.getProvinces()
    if (Array.isArray(response)) {
      provinces.value = response
    }
  } catch (error) {
    ElMessage.error('获取省份列表失败')
  }
}

// 获取城市列表
const fetchCities = async (province: string) => {
  try {
    const response = await schoolApi.getCities(province)
    if (Array.isArray(response)) {
      cities.value = response
    }
  } catch (error) {
    ElMessage.error('获取城市列表失败')
  }
}



// 处理省份改变
const handleProvinceChange = (province: string) => {
  selectedCity.value = ''
  fetchCities(province)
  handleSearch()
}

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1
  fetchSchools()
}

// 处理分页
const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchSchools()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchSchools()
}

// 跳转到学校详情
const goToSchoolDetail = (schoolId: number) => {
  router.push(`/schools/${schoolId}`)
}

onMounted(() => {
  fetchProvinces()
  fetchSchools()
})
</script>

<style scoped>
.school-list {
  padding: 20px;
}

.filters {
  margin-bottom: 20px;
  display: flex;
  gap: 16px;
}

.search-input {
  width: 300px;
}

.school-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.school-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 2px 12px 0 rgba(0,0,0,.1);
}

.school-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.school-header h3 {
  margin: 0;
}

.school-info {
  font-size: 14px;
  color: #666;
}

.school-info p {
  margin: 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style> 