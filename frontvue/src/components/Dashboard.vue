<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h2>数据仪表盘</h2>
      <el-button type="primary" @click="refreshStats">
        <el-icon><Refresh /></el-icon> 刷新数据
      </el-button>
    </div>
    
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>
    
    <div v-else-if="error" class="error-container">
      <el-empty description="获取数据失败，请重试" />
      <el-button type="primary" @click="loadStats">重新加载</el-button>
    </div>
    
    <div v-else class="dashboard-content">
      <!-- 概览卡片 -->
      <div class="overview-cards">
        <el-card class="overview-card">
          <div class="card-content">
            <div class="card-icon school-icon"></div>
            <div class="card-info">
              <h3>学校总数</h3>
              <p class="card-value">{{ dashboardStats.school_stats?.total_schools || 0 }}</p>
            </div>
          </div>
        </el-card>
        
        <el-card class="overview-card">
          <div class="card-content">
            <div class="card-icon forum-icon"></div>
            <div class="card-info">
              <h3>帖子总数</h3>
              <p class="card-value">{{ dashboardStats.forum_stats?.total_posts || 0 }}</p>
            </div>
          </div>
        </el-card>
        
        <el-card class="overview-card">
          <div class="card-content">
            <div class="card-icon event-icon"></div>
            <div class="card-info">
              <h3>活动总数</h3>
              <p class="card-value">{{ dashboardStats.event_stats?.total_events || 0 }}</p>
            </div>
          </div>
        </el-card>
        
        <el-card class="overview-card">
          <div class="card-content">
            <div class="card-icon user-icon"></div>
            <div class="card-info">
              <h3>用户总数</h3>
              <p class="card-value">{{ dashboardStats.user_stats?.total_users || 0 }}</p>
            </div>
          </div>
        </el-card>
      </div>
      
      <!-- 图表区域 -->
      <div class="charts-section">
        <div class="chart-row">
          <!-- 学校类型分布 -->
          <el-card class="chart-card">
            <template #header>
              <div class="chart-header">
                <h3>学校类型分布</h3>
              </div>
            </template>
            <div ref="schoolTypeChart" class="chart"></div>
          </el-card>
          
          <!-- 学校层次分布 -->
          <el-card class="chart-card">
            <template #header>
              <div class="chart-header">
                <h3>学校层次分布</h3>
              </div>
            </template>
            <div ref="schoolLevelChart" class="chart"></div>
          </el-card>
        </div>
        
        <div class="chart-row">
          <!-- 省份分布 -->
          <el-card class="chart-card">
            <template #header>
              <div class="chart-header">
                <h3>省份分布</h3>
              </div>
            </template>
            <div ref="provinceChart" class="chart"></div>
          </el-card>
          
          <!-- 论坛活动 -->
          <el-card class="chart-card">
            <template #header>
              <div class="chart-header">
                <h3>论坛活动</h3>
              </div>
            </template>
            <div ref="forumActivityChart" class="chart"></div>
          </el-card>
        </div>
        
        <div class="chart-row">
          <!-- 活动状态分布 -->
          <el-card class="chart-card">
            <template #header>
              <div class="chart-header">
                <h3>活动状态分布</h3>
              </div>
            </template>
            <div ref="eventStatusChart" class="chart"></div>
          </el-card>
          
          <!-- 用户行为 -->
          <el-card class="chart-card">
            <template #header>
              <div class="chart-header">
                <h3>用户行为</h3>
              </div>
            </template>
            <div ref="userActivityChart" class="chart"></div>
          </el-card>
        </div>
      </div>
      
      <!-- 数据更新时间 -->
      <div class="last-updated">
        <p>最后更新时间: {{ formatDate(dashboardStats.last_updated) }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { schoolApi } from '@/api/school'

// 仪表盘数据
const dashboardStats = ref<any>({
  school_stats: {},
  forum_stats: {},
  event_stats: {},
  user_stats: {},
  last_updated: new Date().toISOString()
})

// 加载状态
const loading = ref(true)
const error = ref(false)

// 图表引用
const schoolTypeChart = ref<HTMLElement | null>(null)
const schoolLevelChart = ref<HTMLElement | null>(null)
const provinceChart = ref<HTMLElement | null>(null)
const forumActivityChart = ref<HTMLElement | null>(null)
const eventStatusChart = ref<HTMLElement | null>(null)
const userActivityChart = ref<HTMLElement | null>(null)

// 图表实例
const chartInstances = ref<echarts.ECharts[]>([])

// 加载统计数据
const loadStats = async () => {
  loading.value = true
  error.value = false
  try {
    const response = await schoolApi.getDashboardStats()
    dashboardStats.value = response
    
    // 延迟渲染图表，确保DOM已更新
    nextTick(() => {
      renderCharts()
    })
  } catch (err) {
    error.value = true
    ElMessage.error('获取统计数据失败')
    console.error('获取统计数据失败:', err)
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshStats = () => {
  loadStats()
}

// 渲染图表
const renderCharts = () => {
  // 销毁现有图表
  chartInstances.value.forEach(chart => chart.dispose())
  chartInstances.value = []
  
  // 渲染学校类型分布
  if (schoolTypeChart.value) {
    const chart = echarts.init(schoolTypeChart.value)
    const option = {
      tooltip: {
        trigger: 'item'
      },
      legend: {
        top: '5%',
        left: 'center'
      },
      series: [
        {
          name: '学校类型',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: '18',
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: dashboardStats.value.school_stats?.type_distribution || []
        }
      ]
    }
    chart.setOption(option)
    chartInstances.value.push(chart)
  }
  
  // 渲染学校层次分布
  if (schoolLevelChart.value) {
    const chart = echarts.init(schoolLevelChart.value)
    const option = {
      tooltip: {
        trigger: 'item'
      },
      legend: {
        top: '5%',
        left: 'center'
      },
      series: [
        {
          name: '学校层次',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: '18',
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: dashboardStats.value.school_stats?.level_distribution || []
        }
      ]
    }
    chart.setOption(option)
    chartInstances.value.push(chart)
  }
  
  // 渲染省份分布
  if (provinceChart.value) {
    const chart = echarts.init(provinceChart.value)
    const data = dashboardStats.value.school_stats?.province_distribution || []
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: data.map((item: any) => item.province),
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '学校数量',
          type: 'bar',
          data: data.map((item: any) => item.count),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#83bff6' },
              { offset: 0.5, color: '#188df0' },
              { offset: 1, color: '#188df0' }
            ])
          }
        }
      ]
    }
    chart.setOption(option)
    chartInstances.value.push(chart)
  }
  
  // 渲染论坛活动
  if (forumActivityChart.value) {
    const chart = echarts.init(forumActivityChart.value)
    const option = {
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: ['帖子', '评论']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: ['最近7天']
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '帖子',
          type: 'line',
          data: [dashboardStats.value.forum_stats?.recent_posts || 0],
          itemStyle: {
            color: '#4361ee'
          }
        },
        {
          name: '评论',
          type: 'line',
          data: [dashboardStats.value.forum_stats?.recent_comments || 0],
          itemStyle: {
            color: '#3a0ca3'
          }
        }
      ]
    }
    chart.setOption(option)
    chartInstances.value.push(chart)
  }
  
  // 渲染活动状态分布
  if (eventStatusChart.value) {
    const chart = echarts.init(eventStatusChart.value)
    const option = {
      tooltip: {
        trigger: 'item'
      },
      legend: {
        top: '5%',
        left: 'center'
      },
      series: [
        {
          name: '活动状态',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: '18',
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: dashboardStats.value.event_stats?.status_distribution || []
        }
      ]
    }
    chart.setOption(option)
    chartInstances.value.push(chart)
  }
  
  // 渲染用户行为
  if (userActivityChart.value) {
    const chart = echarts.init(userActivityChart.value)
    const data = dashboardStats.value.user_stats?.activity_stats || []
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: data.map((item: any) => item.activity_type)
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '行为次数',
          type: 'bar',
          data: data.map((item: any) => item.count),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#f72585' },
              { offset: 0.5, color: '#7209b7' },
              { offset: 1, color: '#3a0ca3' }
            ])
          }
        }
      ]
    }
    chart.setOption(option)
    chartInstances.value.push(chart)
  }
}

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 响应式调整图表大小
const handleResize = () => {
  chartInstances.value.forEach(chart => chart.resize())
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  chartInstances.value.forEach(chart => chart.dispose())
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
  margin: 20px 0;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.dashboard-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.loading-container,
.error-container {
  padding: 40px 0;
  text-align: center;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.overview-card {
  transition: all 0.3s ease;
}

.overview-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-position: center;
  background-size: 30px;
  background-repeat: no-repeat;
}

.school-icon {
  background-color: rgba(67, 97, 238, 0.1);
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82zM12 3L1 9l4 2.18v6L12 21l7-3.82v-6l2-1.18V9l-11-6z"/></svg>');
}

.forum-icon {
  background-color: rgba(76, 201, 240, 0.1);
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234895ef"><path d="M21 6h-2v9H6v2c0 .55.45 1 1 1h11l4 4V7c0-.55-.45-1-1-1zm-4 6V3c0-.55-.45-1-1-1H3c-.55 0-1 .45-1 1v14l4-4h10c.55 0 1-.45 1-1z"/></svg>');
}

.event-icon {
  background-color: rgba(114, 9, 183, 0.1);
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%237209b7"><path d="M19 3h-1V2c0-.55-.45-1-1-1s-1 .45-1 1v1H8V2c0-.55-.45-1-1-1s-1 .45-1 1v1H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM7 10h5v5H7z"/></svg>');
}

.user-icon {
  background-color: rgba(247, 37, 133, 0.1);
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23f72585"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>');
}

.card-info h3 {
  margin: 0 0 5px;
  font-size: 14px;
  color: #666;
  font-weight: normal;
}

.card-value {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.charts-section {
  margin-bottom: 30px;
}

.chart-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.chart-card {
  transition: all 0.3s ease;
}

.chart-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.chart-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.chart {
  width: 100%;
  height: 300px;
}

.last-updated {
  text-align: right;
  font-size: 12px;
  color: #999;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .overview-cards {
    grid-template-columns: 1fr;
  }
  
  .chart-row {
    grid-template-columns: 1fr;
  }
  
  .chart {
    height: 250px;
  }
}
</style>
