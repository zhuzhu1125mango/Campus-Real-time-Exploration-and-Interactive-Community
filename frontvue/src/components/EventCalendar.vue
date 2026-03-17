<template>
  <div class="event-calendar">
    <div class="calendar-header">
      <h2>校园活动日历</h2>
      <div class="filter-container">
        <el-select v-model="schoolFilter" placeholder="选择学校" @change="loadEvents">
          <el-option label="所有学校" value="" />
          <el-option 
            v-for="school in schools" 
            :key="school.id" 
            :label="school.name" 
            :value="school.id" 
          />
        </el-select>
        <el-select v-model="statusFilter" placeholder="活动状态" @change="loadEvents">
          <el-option label="全部" value="" />
          <el-option label="即将开始" value="upcoming" />
          <el-option label="进行中" value="ongoing" />
          <el-option label="已完成" value="completed" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          @change="loadEvents"
        />
      </div>
    </div>

    <!-- 日历视图 -->
    <div class="calendar-view">
      <el-calendar v-model="currentDate">
        <template #dateCell="{ date, data }">
          <div class="calendar-date">
            <span class="date-number">{{ data.day }}</span>
            <div class="events-indicator">
              <el-tag 
                v-for="event in getEventsForDate(date)" 
                :key="event.id"
                size="small"
                :type="getEventTagType(event.status)"
                class="event-tag"
                @click="viewEvent(event)"
              >
                {{ event.title }}
              </el-tag>
            </div>
          </div>
        </template>
      </el-calendar>
    </div>

    <!-- 活动列表 -->
    <div class="event-list">
      <h3>活动列表</h3>
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="3" animated />
      </div>
      <div v-else-if="error" class="error-container">
        <el-empty description="获取活动失败，请重试" />
        <el-button type="primary" @click="loadEvents">重新加载</el-button>
      </div>
      <div v-else-if="events.length === 0" class="empty-container">
        <el-empty description="暂无活动" />
      </div>
      <div v-else class="event-cards">
        <el-card 
          v-for="event in events" 
          :key="event.id"
          class="event-card"
          @click="viewEvent(event)"
        >
          <template #header>
            <div class="event-card-header">
              <h4>{{ event.title }}</h4>
              <el-tag :type="getEventTagType(event.status)">
                {{ getEventStatusText(event.status) }}
              </el-tag>
            </div>
          </template>
          <div class="event-card-body">
            <div class="event-info">
              <el-icon><Time /></el-icon>
              <span>{{ formatDateTime(event.start_time) }} - {{ formatDateTime(event.end_time) }}</span>
            </div>
            <div class="event-info">
              <el-icon><Location /></el-icon>
              <span>{{ event.location }}</span>
            </div>
            <div class="event-info">
              <el-icon><User /></el-icon>
              <span>{{ event.organizer }}</span>
            </div>
            <div class="event-info">
              <el-icon><School /></el-icon>
              <span>{{ event.school }}</span>
            </div>
            <div class="event-description">
              {{ truncateText(event.description, 100) }}
            </div>
            <div class="event-footer">
              <span class="registration-count">
                报名人数: {{ event.registration_count }}
                <span v-if="event.capacity"> / {{ event.capacity }}</span>
              </span>
              <el-button 
                v-if="event.status === 'upcoming' && !event.is_registered" 
                type="primary" 
                size="small"
                @click.stop="registerEvent(event)"
              >
                立即报名
              </el-button>
              <el-button 
                v-else-if="event.is_registered" 
                type="warning" 
                size="small"
                @click.stop="cancelRegistration(event)"
              >
                已报名
              </el-button>
              <el-button 
                v-else 
                type="info" 
                size="small"
                disabled
              >
                查看详情
              </el-button>
            </div>
          </div>
        </el-card>
      </div>
      <div class="pagination" v-if="total > 0">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 活动详情对话框 -->
    <el-dialog
      v-model="showEventDialog"
      :title="selectedEvent?.title || '活动详情'"
      width="80%"
    >
      <div v-if="loadingEvent" class="loading-container">
        <el-skeleton :rows="10" animated />
      </div>
      <div v-else-if="errorEvent" class="error-container">
        <el-empty description="获取活动详情失败" />
        <el-button type="primary" @click="loadEventDetail(selectedEvent.id)">重新加载</el-button>
      </div>
      <div v-else-if="selectedEvent" class="event-detail">
        <div class="event-detail-header">
          <h3>{{ selectedEvent.title }}</h3>
          <el-tag :type="getEventTagType(selectedEvent.status)">
            {{ getEventStatusText(selectedEvent.status) }}
          </el-tag>
        </div>
        <div class="event-detail-info">
          <div class="info-item">
            <el-icon><School /></el-icon>
            <span>学校: {{ selectedEvent.school }}</span>
          </div>
          <div class="info-item">
            <el-icon><Time /></el-icon>
            <span>开始时间: {{ formatDateTime(selectedEvent.start_time) }}</span>
          </div>
          <div class="info-item">
            <el-icon><Time /></el-icon>
            <span>结束时间: {{ formatDateTime(selectedEvent.end_time) }}</span>
          </div>
          <div class="info-item">
            <el-icon><Location /></el-icon>
            <span>地点: {{ selectedEvent.location }}</span>
          </div>
          <div class="info-item">
            <el-icon><User /></el-icon>
            <span>组织者: {{ selectedEvent.organizer }}</span>
          </div>
          <div class="info-item">
            <el-icon><UserFilled /></el-icon>
            <span>报名人数: {{ selectedEvent.registration_count }}
              <span v-if="selectedEvent.capacity"> / {{ selectedEvent.capacity }}</span>
            </span>
          </div>
          <div class="info-item" v-if="selectedEvent.registration_deadline">
            <el-icon><Timer /></el-icon>
            <span>报名截止: {{ formatDateTime(selectedEvent.registration_deadline) }}</span>
          </div>
        </div>
        <div class="event-detail-description">
          <h4>活动描述</h4>
          <p>{{ selectedEvent.description }}</p>
        </div>
        <div class="event-detail-actions">
          <el-button 
            v-if="selectedEvent.status === 'upcoming' && !selectedEvent.is_registered" 
            type="primary"
            @click="registerEvent(selectedEvent)"
          >
            立即报名
          </el-button>
          <el-button 
            v-else-if="selectedEvent.is_registered" 
            type="warning"
            @click="cancelRegistration(selectedEvent)"
          >
            取消报名
          </el-button>
          <el-button 
            v-else 
            type="info"
            disabled
          >
            活动已结束
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { Location, User, School, UserFilled, Timer } from '@element-plus/icons-vue'
import { schoolApi } from '../api/school'

// 筛选条件
const schoolFilter = ref('')
const statusFilter = ref('')
const dateRange = ref<[Date, Date] | null>(null)

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 活动数据
const events = ref<any[]>([])
const loading = ref(false)
const error = ref(false)

// 学校数据
const schools = ref<any[]>([])

// 日历
const currentDate = ref(new Date())

// 活动详情
const selectedEvent = ref<any>(null)
const showEventDialog = ref(false)
const loadingEvent = ref(false)
const errorEvent = ref(false)

// 加载学校列表
const loadSchools = async () => {
  try {
    const response = await schoolApi.getSchools({ pageSize: 100 })
    schools.value = response.results || []
  } catch (err) {
    console.error('加载学校列表失败:', err)
  }
}

// 加载活动列表
const loadEvents = async () => {
  loading.value = true
  error.value = false
  try {
    const params: any = {
      page: currentPage.value,
      pageSize: pageSize.value
    }
    
    if (schoolFilter.value) {
      params.school_id = schoolFilter.value
    }
    
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    
    if (dateRange.value) {
      params.start_date = dateRange.value[0].toISOString().split('T')[0]
      params.end_date = dateRange.value[1].toISOString().split('T')[0]
    }
    
    const response = await schoolApi.getEvents(params)
    events.value = response.results || []
    total.value = response.count || 0
  } catch (err) {
    error.value = true
    ElMessage.error('获取活动失败')
    console.error('获取活动失败:', err)
  } finally {
    loading.value = false
  }
}

// 加载活动详情
const loadEventDetail = async (eventId: number) => {
  loadingEvent.value = true
  errorEvent.value = false
  try {
    const response = await schoolApi.getEvent(eventId)
    selectedEvent.value = response
  } catch (err) {
    errorEvent.value = true
    ElMessage.error('获取活动详情失败')
    console.error('获取活动详情失败:', err)
  } finally {
    loadingEvent.value = false
  }
}

// 查看活动详情
const viewEvent = (event: any) => {
  selectedEvent.value = event
  showEventDialog.value = true
  loadEventDetail(event.id)
}

// 报名活动
const registerEvent = async (event: any) => {
  try {
    await schoolApi.registerEvent(event.id)
    ElNotification.success({
      title: '报名成功',
      message: `您已成功报名 ${event.title}`,
      duration: 3000
    })
    // 重新加载活动详情
    loadEventDetail(event.id)
    // 重新加载活动列表
    loadEvents()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '报名失败，请重试')
    console.error('报名失败:', err)
  }
}

// 取消报名
const cancelRegistration = async (event: any) => {
  try {
    await schoolApi.cancelEventRegistration(event.id)
    ElNotification.success({
      title: '取消成功',
      message: `您已成功取消 ${event.title} 的报名`,
      duration: 3000
    })
    // 重新加载活动详情
    loadEventDetail(event.id)
    // 重新加载活动列表
    loadEvents()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '取消报名失败，请重试')
    console.error('取消报名失败:', err)
  }
}

// 根据日期获取活动
const getEventsForDate = (date: Date) => {
  const dateStr = date.toISOString().split('T')[0]
  return events.value.filter(event => {
    const eventDate = new Date(event.start_time).toISOString().split('T')[0]
    return eventDate === dateStr
  })
}

// 获取活动标签类型
const getEventTagType = (status: string) => {
  switch (status) {
    case 'upcoming':
      return 'info'
    case 'ongoing':
      return 'success'
    case 'completed':
      return 'warning'
    case 'cancelled':
      return 'danger'
    default:
      return 'info'
  }
}

// 获取活动状态文本
const getEventStatusText = (status: string) => {
  switch (status) {
    case 'upcoming':
      return '即将开始'
    case 'ongoing':
      return '进行中'
    case 'completed':
      return '已完成'
    case 'cancelled':
      return '已取消'
    default:
      return status
  }
}

// 格式化日期时间
const formatDateTime = (dateTime: string) => {
  const date = new Date(dateTime)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 截断文本
const truncateText = (text: string, length: number) => {
  if (text.length <= length) {
    return text
  }
  return text.substring(0, length) + '...'
}

// 分页处理
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadEvents()
}

const handleCurrentChange = (current: number) => {
  currentPage.value = current
  loadEvents()
}

// 初始化
onMounted(() => {
  loadSchools()
  loadEvents()
})
</script>

<style scoped>
.event-calendar {
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
  margin: 20px 0;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
}

.calendar-header h2 {
  color: #333;
  margin: 0;
  font-size: 18px;
}

.filter-container {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.calendar-view {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.calendar-date {
  position: relative;
  height: 100px;
  padding: 5px;
}

.date-number {
  font-size: 14px;
  font-weight: 500;
}

.events-indicator {
  margin-top: 5px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.event-tag {
  cursor: pointer;
  font-size: 10px;
  padding: 2px 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.event-list {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.event-list h3 {
  color: #333;
  margin-bottom: 20px;
  font-size: 16px;
}

.loading-container,
.error-container,
.empty-container {
  padding: 40px 0;
  text-align: center;
}

.event-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.event-card {
  cursor: pointer;
  transition: all 0.3s ease;
}

.event-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.event-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.event-card-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
}

.event-card-body {
  padding: 10px 0;
}

.event-info {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 8px;
  font-size: 12px;
  color: #666;
}

.event-description {
  margin: 10px 0;
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}

.event-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  font-size: 12px;
  color: #999;
}

.registration-count {
  font-size: 12px;
}

.pagination {
  margin-top: 20px;
  text-align: center;
}

.event-detail {
  padding: 10px 0;
}

.event-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.event-detail-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
}

.event-detail-info {
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  font-size: 14px;
}

.event-detail-description {
  margin-bottom: 20px;
}

.event-detail-description h4 {
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 500;
}

.event-detail-description p {
  line-height: 1.6;
  color: #333;
}

.event-detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .calendar-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-container {
    width: 100%;
  }

  .event-cards {
    grid-template-columns: 1fr;
  }

  .event-detail-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style>
