import request from '@/utils/request'
import type { School, SchoolRating, SchoolQueryParams, SchoolListResponse, ImportCsvResponse } from '@/types/school'

export interface SchoolFilterOptions {
  types: { [key: string]: string }
  levels: { [key: string]: string }
}

export const schoolApi = {
  // 获取学校列表
  getSchools(params: SchoolQueryParams) {
    return request.get<SchoolListResponse>('/api/schools/', { params })
  },

  // 获取学校详情
  getSchool(id: number) {
    return request.get<School>(`/api/schools/${id}/`)
  },

  // 获取省份列表
  getProvinces() {
    return request.get<string[]>('/api/schools/provinces/')
  },

  // 获取城市列表
  getCities(province: string) {
    return request.get<string[]>('/api/schools/cities/', { params: { province } })
  },

  // 获取学校类型列表
  getSchoolTypes() {
    return request.get<{ [key: string]: string }>('/api/schools/types/')
  },

  // 获取学校层次列表
  getSchoolLevels() {
    return request.get<{ [key: string]: string }>('/api/schools/levels/')
  },

  // 获取学校评分列表
  getSchoolRatings(schoolId: number, params?: { page?: number, pageSize?: number }) {
    return request.get<{ results: SchoolRating[], count: number }>(
      `/api/schools/${schoolId}/ratings/`,
      { params }
    )
  },

  // 评分学校
  rateSchool(schoolId: number, data: { score: number, comment: string }) {
    return request.post(`/api/schools/${schoolId}/rate/`, data)
  },
  
  // 导入学校CSV数据
  importSchoolsCsv(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    
    return request.post<ImportCsvResponse>('/api/schools/import_csv/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
} 