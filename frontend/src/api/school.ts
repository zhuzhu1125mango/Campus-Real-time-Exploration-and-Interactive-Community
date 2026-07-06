import request from '@/utils/request'
import type {
  School, SchoolRating, SchoolQueryParams, SchoolListResponse, ImportCsvResponse,
  EventListResponse, Event as SchoolEvent, Place, CheckIn, NearbyPlaceParams, NearbyEventParams, PlaceParams
} from '@/types/school'
import type { Board } from '@/types/forum'

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

  // 获取学校论坛（返回 forum.Board 数据）
  getSchoolForum(id: number) {
    return request.get<Board>(`/schools/${id}/forums/`)
  },

  // 获取论坛帖子列表
  getForumPosts(forumId: number, params?: { page?: number, page_size?: number }) {
    return request.get<{ count: number; next: string | null; previous: string | null; results: any[] }>(`/schools/forums/${forumId}/posts/`, { params })
  },

  // 创建论坛帖子
  createForumPost(data: { forum: number; title: string; content: string }) {
    return request.post<any>('/schools/posts/', data)
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

  // 收藏学校
  favoriteSchool(schoolId: number) {
    return request.post<{ detail: string }>(`/schools/${schoolId}/favorite/`)
  },

  // 取消收藏学校
  unfavoriteSchool(schoolId: number) {
    return request.post<{ detail: string }>(`/schools/${schoolId}/unfavorite/`)
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
  },

  // 探索：获取附近地点
  getNearbyPlaces(params: NearbyPlaceParams) {
    return request.get<Place[]>('/schools/explore/nearby_places/', { params })
  },

  // 探索：获取附近活动
  getNearbyEvents(params: NearbyEventParams) {
    return request.get<SchoolEvent[]>('/schools/explore/nearby_events/', { params })
  },

  // 探索：获取地点列表
  getPlaces(params?: PlaceParams) {
    return request.get<Place[]>('/schools/explore/places/', { params })
  },

  // 探索：在指定地点打卡
  checkIn(placeId: number, data?: { latitude?: number; longitude?: number; note?: string }) {
    return request.post<CheckIn>('/schools/explore/checkin/', { place_id: placeId, ...data })
  },

  // 探索：获取我的打卡记录
  getMyCheckIns() {
    return request.get<CheckIn[]>('/schools/explore/my_checkins/')
  }
} 