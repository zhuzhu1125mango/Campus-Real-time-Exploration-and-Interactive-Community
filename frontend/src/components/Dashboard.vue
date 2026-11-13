<template>
  <div class="dashboard">
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <div v-else-if="error" class="error-container">
      <el-empty description="获取数据失败，请重试" />
      <button class="btn btn-primary" @click="loadStats">重新加载</button>
    </div>

    <div v-else class="dashboard-content">
      <div class="dashboard-toolbar">
        <button class="btn btn-primary" @click="refreshStats">
          <span class="i-ep-refresh" /> 刷新数据
        </button>
      </div>

      <!-- 概览卡片 -->
      <div class="overview-cards">
        <GlassCard :hover="false" class="overview-card">
          <div class="card-content">
            <span class="card-icon school-icon i-ep-school" />
            <div class="card-info">
              <h3>学校总数</h3>
              <p class="card-value">{{ dashboardStats.school_stats?.total_schools || 0 }}</p>
            </div>
          </div>
        </GlassCard>

        <GlassCard :hover="false" class="overview-card">
          <div class="card-content">
            <span class="card-icon forum-icon i-ep-chat-dot-round" />
            <div class="card-info">
              <h3>帖子总数</h3>
              <p class="card-value">{{ dashboardStats.forum_stats?.total_posts || 0 }}</p>
            </div>
          </div>
        </GlassCard>

        <GlassCard :hover="false" class="overview-card">
          <div class="card-content">
            <span class="card-icon event-icon i-ep-calendar" />
            <div class="card-info">
              <h3>活动总数</h3>
              <p class="card-value">{{ dashboardStats.event_stats?.total_events || 0 }}</p>
            </div>
          </div>
        </GlassCard>

        <GlassCard :hover="false" class="overview-card">
          <div class="card-content">
            <span class="card-icon user-icon i-ep-user" />
            <div class="card-info">
              <h3>用户总数</h3>
              <p class="card-value">{{ dashboardStats.user_stats?.total_users || 0 }}</p>
            </div>
          </div>
        </GlassCard>
      </div>

      <!-- 图表区域 -->
      <div class="charts-section">
        <div class="chart-row">
          <GlassCard :hover="false" title="学校类型分布" class="chart-card">
            <div ref="schoolTypeChart" class="chart"></div>
          </GlassCard>

          <GlassCard :hover="false" title="学校层次分布" class="chart-card">
            <div ref="schoolLevelChart" class="chart"></div>
          </GlassCard>
        </div>

        <div class="chart-row">
          <GlassCard :hover="false" title="省份分布" class="chart-card">
            <div ref="provinceChart" class="chart"></div>
          </GlassCard>

          <GlassCard :hover="false" title="论坛活动" class="chart-card">
            <div ref="forumActivityChart" class="chart"></div>
          </GlassCard>
        </div>

        <div class="chart-row">
          <GlassCard :hover="false" title="活动状态分布" class="chart-card">
            <div ref="eventStatusChart" class="chart"></div>
          </GlassCard>

          <GlassCard :hover="false" title="用户行为" class="chart-card">
            <div ref="userActivityChart" class="chart"></div>
          </GlassCard>
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
import { schoolApi } from '@/api/school'
import GlassCard from '@/components/GlassCard.vue'
import type { DashboardStats } from '@/types/school'

// 仪表盘数据
const dashboardStats = ref<DashboardStats>({
  school_stats: {
    total_schools: 0,
    type_distribution: [],
    level_distribution: [],
    province_distribution: []
  },
  forum_stats: {
    total_posts: 0,
    recent_posts: 0,
    recent_comments: 0
  },
  event_stats: {
    total_events: 0,
    status_distribution: []
  },
  user_stats: {
    total_users: 0,
    activity_stats: []
  },
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
const chartInstances = ref<any[]>([])

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
const renderCharts = async () => {
  // 动态加载按需引入的 echarts，减少 chunk 体积
  const echarts: any = await import('@/utils/echarts')

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
        data: data.map((item) => item.province),
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
          data: data.map((item) => item.count),
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
        data: data.map((item) => item.activity_type)
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '行为次数',
          type: 'bar',
          data: data.map((item) => item.count),
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
  width: 100%;
}

.loading-container,
.error-container {
  padding: var(--space-10) 0;
  text-align: center;
}

.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
}

.dashboard-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: var(--space-5);
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-5);
  margin-bottom: var(--space-6);
}

.card-content {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.75rem;
  flex-shrink: 0;
}

.school-icon {
  background-color: var(--primary-100);
  color: var(--primary-600);
}

.forum-icon {
  background-color: var(--info-bg);
  color: var(--info-color);
}

.event-icon {
  background-color: var(--accent-orange-light);
  color: var(--accent-orange);
}

.user-icon {
  background-color: var(--error-bg);
  color: var(--error-color);
}

.card-info h3 {
  margin: 0 0 var(--space-1);
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.card-value {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.charts-section {
  margin-bottom: var(--space-6);
}

.chart-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: var(--space-5);
  margin-bottom: var(--space-5);
}

.chart {
  width: 100%;
  height: 300px;
}

.last-updated {
  text-align: right;
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin-top: var(--space-5);
}

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

.btn-primary:hover {
  background-color: var(--primary-700);
}

.btn-secondary {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background-color: var(--border-color);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

  .dashboard-toolbar {
    justify-content: flex-start;
  }

  .last-updated {
    text-align: left;
  }
}
</style>
