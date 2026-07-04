<template>
  <div class="school-comparison">
    <div class="comparison-header">
      <h2>院校对比</h2>
      <p>选择2-4所院校进行多维度对比</p>
    </div>

    <!-- 院校选择器 -->
    <div class="school-selector">
      <h3>选择院校</h3>
      <div class="selector-container">
        <div 
          v-for="(school, index) in selectedSchools" 
          :key="school.id || index"
          class="school-select-item"
        >
          <el-select
            v-model="selectedSchools[index]"
            placeholder="选择院校"
            filterable
            remote
            :remote-method="querySchools"
            :loading="loading"
            @change="handleSchoolChange(index)"
          >
            <el-option
              v-for="item in schoolOptions"
              :key="item.id"
              :label="item.name"
              :value="item"
            >
              <div class="school-option">
                <span>{{ item.name }}</span>
                <span class="school-info">{{ item.province }} · {{ item.city }}</span>
              </div>
            </el-option>
          </el-select>
          <el-button 
            v-if="index > 0" 
            type="danger" 
            circle 
            @click="removeSchool(index)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
        <el-button 
          v-if="selectedSchools.length < 4" 
          type="primary" 
          @click="addSchool"
        >
          <el-icon><Plus /></el-icon> 添加院校
        </el-button>
      </div>
    </div>

    <!-- 对比字段选择 -->
    <div class="field-selector" v-if="selectedSchools.length >= 2">
      <h3>选择对比字段</h3>
      <el-checkbox-group v-model="selectedFields">
        <el-checkbox 
          v-for="field in availableFields" 
          :key="field.key"
          :label="field.key"
        >
          {{ field.label }}
        </el-checkbox>
      </el-checkbox-group>
    </div>

    <!-- 对比按钮 -->
    <div class="compare-button" v-if="selectedSchools.length >= 2">
      <el-button 
        type="primary" 
        size="large" 
        @click="compareSchools"
        :loading="comparing"
        :disabled="comparing"
      >
        开始对比
      </el-button>
    </div>

    <!-- 对比结果 -->
    <div class="comparison-result" v-if="showResult">
      <h3>对比结果</h3>
      
      <!-- 表格对比 -->
      <div class="result-table">
        <el-table :data="comparisonData" style="width: 100%">
          <el-table-column prop="field" label="对比项" width="180" />
          <el-table-column 
            v-for="(school, index) in compareResult.schools" 
            :key="school.id"
            :label="school.name"
          >
            <template #default="scope">
              <div v-if="scope.row.type === 'text'">
                {{ scope.row[`value${index}`] }}
              </div>
              <div v-else-if="scope.row.type === 'number'" class="number-value">
                {{ scope.row[`value${index}`] }}
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 图表对比 -->
      <div class="result-charts" v-if="compareResult.schools.length > 1">
        <h4>数据可视化</h4>
        <div class="chart-container">
          <div v-for="field in selectedFields" :key="field" class="chart-item">
            <h5>{{ getFieldLabel(field) }}</h5>
            <div ref="charts" :id="`chart-${field}`" class="chart"></div>
          </div>
        </div>
      </div>

      <!-- 专业对比 -->
      <div class="majors-comparison" v-if="compareResult.schools.length > 0">
        <h4>专业设置对比</h4>
        <div class="majors-container">
          <div 
            v-for="school in compareResult.schools" 
            :key="school.id"
            class="school-majors"
          >
            <h5>{{ school.name }} 热门专业</h5>
            <el-tag 
              v-for="major in school.majors" 
              :key="major.id"
              class="major-tag"
              size="small"
            >
              {{ major.name }}
            </el-tag>
          </div>
        </div>
      </div>

      <!-- 录取分数线对比 -->
      <div class="scores-comparison" v-if="compareResult.schools.length > 0">
        <h4>录取分数线对比</h4>
        <div class="scores-container">
          <div 
            v-for="school in compareResult.schools" 
            :key="school.id"
            class="school-scores"
          >
            <h5>{{ school.name }} 近年录取分数线</h5>
            <el-table :data="school.admission_scores" style="width: 100%">
              <el-table-column prop="year" label="年份" width="80" />
              <el-table-column prop="province" label="省份" width="120" />
              <el-table-column prop="score_type" label="科类" width="100" />
              <el-table-column prop="min_score" label="最低分" width="100" />
              <el-table-column prop="avg_score" label="平均分" width="100" />
              <el-table-column prop="ranking" label="排名" width="100" />
            </el-table>
          </div>
        </div>
      </div>

      <!-- 导出按钮 -->
      <div class="export-buttons">
        <el-button @click="exportComparison">
          <el-icon><Download /></el-icon> 导出对比结果
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { Delete, Plus, Download } from '@element-plus/icons-vue'
// import * as echarts from 'echarts'
import { schoolApi } from '../api/school'

// 院校选择相关
const selectedSchools = ref<any[]>([{}, {}])
const schoolOptions = ref<any[]>([])
const loading = ref(false)
const comparing = ref(false)

// 对比字段相关
const availableFields = ref([
  { key: 'name', label: '学校名称', type: 'text' },
  { key: 'abbreviation', label: '简称', type: 'text' },
  { key: 'province', label: '省份', type: 'text' },
  { key: 'city', label: '城市', type: 'text' },
  { key: 'school_type', label: '学校类型', type: 'text' },
  { key: 'school_level', label: '办学层次', type: 'text' },
  { key: 'founded_year', label: '建校时间', type: 'number' },
  { key: 'national_rank', label: '全国排名', type: 'number' },
  { key: 'student_count', label: '学生人数', type: 'number' },
  { key: 'faculty_count', label: '教职工人数', type: 'number' },
  { key: 'campus_area', label: '校园面积', type: 'number' },
  { key: 'average_rating', label: '平均评分', type: 'number' }
])
const selectedFields = ref<string[]>([
  'name', 'abbreviation', 'province', 'school_type', 'school_level', 
  'national_rank', 'average_rating'
])

// 对比结果相关
const compareResult = ref<any>({ schools: [], fields: [] })
const showResult = ref(false)
const comparisonData = ref<any[]>([])

// 搜索院校
const querySchools = async (query: string) => {
  if (query) {
    loading.value = true
    try {
    const response = await schoolApi.getSchools({ search: query, pageSize: 20 })
    schoolOptions.value = (response as any).results || []
  } catch (error) {
      ElMessage.error('搜索院校失败')
      console.error('搜索院校失败:', error)
    } finally {
      loading.value = false
    }
  } else {
    schoolOptions.value = []
  }
}

// 添加院校
const addSchool = () => {
  if (selectedSchools.value.length < 4) {
    selectedSchools.value.push({})
  }
}

// 移除院校
const removeSchool = (index: number) => {
  selectedSchools.value.splice(index, 1)
  if (selectedSchools.value.length < 2) {
    showResult.value = false
  }
}

// 处理院校选择变化
const handleSchoolChange = (index: number) => {
  // 检查是否有重复选择
  const selectedIds = selectedSchools.value
    .filter(school => school.id)
    .map(school => school.id)
  
  const uniqueIds = [...new Set(selectedIds)]
  if (uniqueIds.length !== selectedIds.length) {
    ElMessage.warning('不能选择重复的院校')
    selectedSchools.value[index] = {}
  }
}

// 获取字段标签
const getFieldLabel = (fieldKey: string) => {
  const field = availableFields.value.find(f => f.key === fieldKey)
  return field ? field.label : fieldKey
}

// 准备对比数据
const prepareComparisonData = () => {
  const data: any[] = []
  
  selectedFields.value.forEach(fieldKey => {
    const field = availableFields.value.find(f => f.key === fieldKey)
    if (field) {
      const row: any = {
        field: field.label,
        type: field.type
      }
      
      compareResult.value.schools.forEach((school: any, index: number) => {
        row[`value${index}`] = school[fieldKey] || '-'
      })
      
      data.push(row)
    }
  })
  
  return data
}

// 渲染图表
const renderCharts = () => {
  // 暂时注释掉图表渲染，因为echarts未安装
  // nextTick(() => {
  //   selectedFields.value.forEach(fieldKey => {
  //     const field = availableFields.value.find(f => f.key === fieldKey)
  //     if (field && field.type === 'number') {
  //       const chartDom = document.getElementById(`chart-${fieldKey}`)
  //       if (chartDom) {
  //         const chart = echarts.init(chartDom)
  //         
  //         const xAxisData = compareResult.value.schools.map((school: any) => school.name)
  //         const seriesData = compareResult.value.schools.map((school: any) => school[fieldKey] || 0)
  //         
  //         const option = {
  //           tooltip: {
  //             trigger: 'axis',
  //             axisPointer: {
  //               type: 'shadow'
  //             }
  //           },
  //           xAxis: {
  //             type: 'category',
  //             data: xAxisData
  //           },
  //           yAxis: {
  //             type: 'value'
  //           },
  //           series: [
  //             {
  //               data: seriesData,
  //               type: 'bar',
  //               itemStyle: {
  //                 color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
  //                   { offset: 0, color: '#83bff6' },
  //                   { offset: 0.5, color: '#188df0' },
  //                   { offset: 1, color: '#188df0' }
  //                 ])
  //               }
  //             }
  //           ]
  //         }
  //         
  //         chart.setOption(option)
  //         
  //         // 响应式调整
  //         window.addEventListener('resize', () => {
  //           chart.resize()
  //         })
  //       }
  //     }
  //   })
  // })
}

// 对比院校
const compareSchools = async () => {
  // 检查是否选择了至少2所院校
  const validSchools = selectedSchools.value.filter(school => school.id)
  if (validSchools.length < 2) {
    ElMessage.warning('至少需要选择2所院校进行对比')
    return
  }
  
  comparing.value = true
  try {
    const schoolIds = validSchools.map(school => school.id)
    const response = await schoolApi.compareSchools({
      school_ids: schoolIds,
      comparison_fields: selectedFields.value
    })
    
    compareResult.value = response
    comparisonData.value = prepareComparisonData()
    showResult.value = true
    
    // 渲染图表
    renderCharts()
    
    ElNotification.success({
      title: '对比成功',
      message: `已完成 ${validSchools.length} 所院校的对比`,
      duration: 3000
    })
  } catch (error) {
    ElMessage.error('对比失败，请重试')
    console.error('对比失败:', error)
  } finally {
    comparing.value = false
  }
}

// 导出对比结果
const exportComparison = () => {
  // 这里可以实现导出功能，例如导出为Excel或PDF
  ElMessage.info('导出功能开发中')
}

// 初始化
onMounted(() => {
  // 可以在这里添加初始化逻辑
})
</script>

<style scoped>
.school-comparison {
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
  margin: 20px 0;
}

.comparison-header {
  margin-bottom: 30px;
  text-align: center;
}

.comparison-header h2 {
  color: #333;
  margin-bottom: 10px;
}

.comparison-header p {
  color: #666;
  font-size: 14px;
}

.school-selector {
  margin-bottom: 30px;
}

.school-selector h3,
.field-selector h3,
.comparison-result h3 {
  color: #333;
  margin-bottom: 15px;
  font-size: 16px;
}

.selector-container {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  align-items: flex-end;
}

.school-select-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.school-option {
  display: flex;
  flex-direction: column;
}

.school-info {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.field-selector {
  margin-bottom: 20px;
}

.field-selector .el-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.compare-button {
  margin-bottom: 30px;
  text-align: center;
}

.comparison-result {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.result-table {
  margin-bottom: 30px;
  overflow-x: auto;
}

.number-value {
  text-align: center;
  font-weight: 500;
}

.result-charts {
  margin-bottom: 30px;
}

.result-charts h4 {
  color: #333;
  margin-bottom: 15px;
  font-size: 14px;
}

.chart-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}

.chart-item h5 {
  color: #666;
  margin-bottom: 10px;
  font-size: 12px;
}

.chart {
  width: 100%;
  height: 300px;
}

.majors-comparison,
.scores-comparison {
  margin-bottom: 30px;
}

.majors-comparison h4,
.scores-comparison h4 {
  color: #333;
  margin-bottom: 15px;
  font-size: 14px;
}

.majors-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.school-majors h5,
.school-scores h5 {
  color: #666;
  margin-bottom: 10px;
  font-size: 12px;
}

.major-tag {
  margin: 5px;
}

.scores-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 20px;
}

.export-buttons {
  margin-top: 30px;
  text-align: center;
}
</style>
