import request from '@/utils/request'
import type { School, SchoolRating, SchoolQueryParams, SchoolListResponse, ImportCsvResponse, EventListResponse } from '@/types/school'

export interface SchoolFilterOptions {
  types: { [key: string]: string }
  levels: { [key: string]: string }
}

export const schoolApi = {
  // 获取学校列表
  getSchools(params: SchoolQueryParams) {
    // 转换pageSize为page_size以匹配后端API
    const transformedParams = {
      ...params,
      page_size: params.pageSize,
    }
    // 删除pageSize参数，避免重复
    delete transformedParams.pageSize
    return request.get<SchoolListResponse>('/schools/', { params: transformedParams })
  },

  // 获取学校详情
  getSchool(id: number) {
    return request.get<School>(`/schools/${id}/`)
  },

  // 获取省份列表
  getProvinces() {
    return request.get<string[]>('/schools/provinces/')
  },

  // 获取城市列表
  getCities(province: string) {
    return request.get<string[]>('/schools/cities/', { params: { province } })
  },

  // 获取学校类型列表
  getSchoolTypes() {
    return request.get<{ [key: string]: string }>('/schools/types/')
  },

  // 获取学校层次列表
  getSchoolLevels() {
    return request.get<{ [key: string]: string }>('/schools/levels/')
  },

  // 获取学校评分列表
  getSchoolRatings(schoolId: number, params?: { page?: number, pageSize?: number }) {
    return request.get<{ results: SchoolRating[], count: number }>(
      `/schools/${schoolId}/ratings/`,
      { params }
    )
  },

  // 评分学校
  rateSchool(schoolId: number, data: { rating: number, comment: string }) {
    return request.post(`/schools/${schoolId}/rate/`, data)
  },
  
  // 导入学校CSV数据
  importSchoolsCsv(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    
    return request.post<ImportCsvResponse>('/schools/import_csv/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 对比学校
  compareSchools(data: { school_ids: number[], comparison_fields: string[] }) {
    return request.post('/schools/compare/', data)
  },

  // 记录用户行为
  logUserActivity(data: { activity_type: string, target_type: string, target_id: number, metadata?: any }) {
    return request.post('/schools/log-activity/', data)
  },

  // 获取个性化推荐
  getRecommendations(params?: { type?: string, limit?: number }) {
    return request.get<any>('/schools/recommendations/', { params })
  },

  // 获取活动列表
  getEvents(params?: { school_id?: number, start_date?: string, end_date?: string, status?: string, page?: number, pageSize?: number }) {
    return request.get<EventListResponse>('/schools/events/', { params })
  },

  // 获取活动详情
  getEvent(id: number) {
    return request.get(`/schools/events/${id}/`)
  },

  // 报名活动
  registerEvent(id: number, data?: { metadata?: any }) {
    return request.post(`/schools/events/${id}/register/`, data)
  },

  // 取消报名
  cancelEventRegistration(id: number) {
    return request.post(`/schools/events/${id}/cancel_registration/`)
  },

  // 获取用户的活动报名记录
  getEventRegistrations(params?: { page?: number, pageSize?: number }) {
    return request.get('/schools/event-registrations/', { params })
  },

  // 获取学校统计数据
  getSchoolStats() {
    return request.get('/schools/stats/school/')
  },

  // 获取论坛统计数据
  getForumStats() {
    return request.get('/schools/stats/forum/')
  },

  // 获取活动统计数据
  getEventStats() {
    return request.get('/schools/stats/event/')
  },

  // 获取用户统计数据
  getUserStats() {
    return request.get('/schools/stats/user/')
  },

  // 获取仪表盘综合统计数据
  getDashboardStats() {
    return request.get('/schools/stats/dashboard/')
  }
} 