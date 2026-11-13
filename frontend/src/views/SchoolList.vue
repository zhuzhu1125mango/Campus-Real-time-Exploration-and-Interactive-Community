<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { schoolApi } from '@/api/school'
import type { School } from '@/types/school'
import TheSearch from '@/components/common/TheSearch.vue'
import GlassCard from '@/components/GlassCard.vue'
import SectionHeader from '@/components/SectionHeader.vue'

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

<template>
  <div class="school-list container page-padding">
    <SectionHeader
      title="学校列表"
      subtitle="发现院校、浏览校园信息与社区"
      icon="i-mdi-school-outline"
    />

    <GlassCard class="filter-card" :hover="false">
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
    </GlassCard>

    <el-row :gutter="20" class="school-grid">
      <el-col v-for="school in schools" :key="school.id" :xs="24" :sm="12" :md="8" :lg="6">
        <GlassCard class="school-card" hover @click="goToSchoolDetail(school.id)">
          <div class="school-header">
            <h3 class="school-name">{{ school.name }}</h3>
            <span class="school-tag">{{ school.school_type }}</span>
          </div>
          <div class="school-info">
            <p>
              <span class="info-icon i-mdi-map-marker-outline" />
              {{ school.province }} {{ school.city }}
            </p>
            <p>
              <span class="info-icon i-mdi-school" />
              {{ school.school_level }}
            </p>
            <p>
              <span class="info-icon i-mdi-information-outline" />
              {{ school.introduction || '暂无描述' }}
            </p>
          </div>
        </GlassCard>
      </el-col>
    </el-row>

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

<style scoped>
.school-list {
  max-width: 1280px;
}

.filter-card {
  margin-bottom: var(--space-6);
}

.filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-4);
}

.search-input {
  width: 300px;
}

.school-grid {
  margin-bottom: var(--space-6);
}

.school-card {
  margin-bottom: var(--space-5);
  cursor: pointer;
}

.school-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.school-name {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
}

.school-tag {
  flex-shrink: 0;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--primary-600);
  background: var(--primary-50);
  padding: 2px 10px;
  border-radius: var(--radius-full);
}

.dark .school-tag {
  color: var(--primary-400);
  background: rgba(37, 99, 235, 0.15);
}

.school-info {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.school-info p {
  margin: var(--space-2) 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  line-height: 1.5;
}

.info-icon {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  color: var(--primary-500);
}

.dark .info-icon {
  color: var(--primary-400);
}

.pagination {
  display: flex;
  justify-content: center;
  padding: var(--space-4) 0;
}

@media (max-width: 640px) {
  .filters {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input,
  .filters :deep(.el-select) {
    width: 100%;
  }
}
</style>
