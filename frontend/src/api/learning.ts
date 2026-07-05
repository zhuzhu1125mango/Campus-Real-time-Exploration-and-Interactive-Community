import request from '../utils/request'
import type { Course } from '../types/learning'

export const learningApi = {
  // 课程相关API
  
  // 获取课程列表
  getCourses(params?: { page?: number; category?: number | string; is_free?: boolean | string; search?: string; ordering?: string }): Promise<{ count: number; next: string | null; previous: string | null; results: Course[] }> {
    return request.get('/learning/courses/', { params })
  },
  
  // 获取课程详情
  getCourseDetail(courseId: number | string): Promise<Course> {
    return request.get(`/learning/courses/${courseId}/`)
  },
  
  // 创建课程
  createCourse(data: FormData | Record<string, any>): Promise<Course> {
    return request.post('/learning/courses/', data)
  },
  
  // 更新课程
  updateCourse(courseId: number | string, data: FormData | Record<string, any>): Promise<Course> {
    return request.put(`/learning/courses/${courseId}/`, data)
  },
  
  // 发布课程
  publishCourse(courseId: number | string): Promise<{ status: string }> {
    return request.post(`/learning/courses/${courseId}/publish/`)
  },
  
  // 取消发布课程
  unpublishCourse(courseId: number | string): Promise<{ status: string }> {
    return request.post(`/learning/courses/${courseId}/unpublish/`)
  },
  
  // 获取课程章节
  getCourseChapters(courseId: number | string): Promise<{ count: number; next: string | null; previous: string | null; results: any[] }> {
    return request.get(`/learning/courses/${courseId}/chapters/`)
  },
  
  // 获取课程课时
  getCourseLessons(courseId: number | string): Promise<{ count: number; next: string | null; previous: string | null; results: any[] }> {
    return request.get(`/learning/courses/${courseId}/lessons/`)
  },
  
  // 获取课程资源
  getCourseResources(courseId: number | string): Promise<{ count: number; next: string | null; previous: string | null; results: any[] }> {
    return request.get(`/learning/courses/${courseId}/resources/`)
  },
  
  // 获取课程评价
  getCourseReviews(courseId: number | string): Promise<{ count: number; next: string | null; previous: string | null; results: any[] }> {
    return request.get(`/learning/courses/${courseId}/reviews/`)
  },
  
  // 章节相关API
  
  // 获取章节列表
  getChapters(params?: { course?: number; page?: number }): Promise<{ count: number; next: string | null; previous: string | null; results: any[] }> {
    return request.get('/learning/chapters/', { params })
  },
  
  // 获取章节详情
  getChapterDetail(chapterId: number | string): Promise<any> {
    return request.get(`/learning/chapters/${chapterId}/`)
  },
  
  // 创建章节
  createChapter(data: { course: number; title: string; description?: string; order?: number }): Promise<any> {
    return request.post('/learning/chapters/', data)
  },
  
  // 更新章节
  updateChapter(chapterId: number | string, data: { title?: string; description?: string; order?: number }): Promise<any> {
    return request.put(`/learning/chapters/${chapterId}/`, data)
  },
  
  // 获取章节课时
  getChapterLessons(chapterId: number | string): Promise<{ count: number; next: string | null; previous: string | null; results: any[] }> {
    return request.get(`/learning/chapters/${chapterId}/lessons/`)
  },
  
  // 课时相关API
  
  // 获取课时列表
  getLessons(params?: { chapter?: number; page?: number }): Promise<{ count: number; next: string | null; previous: string | null; results: any[] }> {
    return request.get('/learning/lessons/', { params })
  },
  
  // 获取课时详情
  getLessonDetail(lessonId: number | string): Promise<any> {
    return request.get(`/learning/lessons/${lessonId}/`)
  },
  
  // 创建课时
  createLesson(data: { chapter: number; title: string; description?: string; content?: string; video_url?: string; duration?: string; is_free?: boolean; order?: number }): Promise<any> {
    return request.post('/learning/lessons/', data)
  },
  
  // 更新课时
  updateLesson(lessonId: number | string, data: { title?: string; description?: string; content?: string; video_url?: string; duration?: string; is_free?: boolean; order?: number }): Promise<any> {
    return request.put(`/learning/lessons/${lessonId}/`, data)
  },
  
  // 增加课时观看次数
  incrementLessonView(lessonId: number | string): Promise<{ status: string }> {
    return request.post(`/learning/lessons/${lessonId}/increment_view/`)
  },
  
  // 报名相关API
  
  // 获取报名列表
  getEnrollments(params?: { user?: number; course?: number; page?: number }): Promise<{ count: number; next: string | null; previous: string | null; results: any[] }> {
    return request.get('/learning/enrollments/', { params })
  },
  
  // 获取报名详情
  getEnrollmentDetail(enrollmentId: number | string): Promise<any> {
    return request.get(`/learning/enrollments/${enrollmentId}/`)
  },
  
  // 报名课程
  enrollCourse(courseId: number): Promise<any> {
    return request.post('/learning/enrollments/', { course: courseId })
  },
  
  // 获取报名进度
  getEnrollmentProgress(enrollmentId: number | string): Promise<{ count: number; next: string | null; previous: string | null; results: any[] }> {
    return request.get(`/learning/enrollments/${enrollmentId}/progress/`)
  },
  
  // 完成课程
  completeCourse(enrollmentId: number | string): Promise<{ status: string }> {
    return request.post(`/learning/enrollments/${enrollmentId}/complete/`)
  },
  
  // 进度相关API
  
  // 获取进度列表
  getProgresses(params?: { enrollment?: number; lesson?: number; page?: number }): Promise<{ count: number; next: string | null; previous: string | null; results: any[] }> {
    return request.get('/learning/progresses/', { params })
  },
  
  // 获取进度详情
  getProgressDetail(progressId: number | string): Promise<any> {
    return request.get(`/learning/progresses/${progressId}/`)
  },
  
  // 更新进度
  updateProgress(progressId: number | string, data: { is_completed?: boolean; last_watched_at?: string; watched_duration?: number; last_position?: number }): Promise<any> {
    return request.put(`/learning/progresses/${progressId}/`, data)
  },

  // 创建或更新课时进度
  recordProgress(data: { enrollment: number; lesson: number; is_completed?: boolean; last_watched_at?: string; watched_duration?: number; last_position?: number }): Promise<any> {
    return request.post('/learning/progresses/record/', data)
  },
  
  // 评价相关API
  
  // 获取评价列表
  getReviews(params?: { user?: number; course?: number; page?: number }): Promise<{ count: number; next: string | null; previous: string | null; results: any[] }> {
    return request.get('/learning/reviews/', { params })
  },
  
  // 获取评价详情
  getReviewDetail(reviewId: number | string): Promise<any> {
    return request.get(`/learning/reviews/${reviewId}/`)
  },
  
  // 创建评价
  createReview(data: { course: number; rating: number; comment?: string }): Promise<any> {
    return request.post('/learning/reviews/', data)
  },
  
  // 批准评价
  approveReview(reviewId: number | string): Promise<{ status: string }> {
    return request.post(`/learning/reviews/${reviewId}/approve/`)
  },
  
  // 拒绝评价
  disapproveReview(reviewId: number | string): Promise<{ status: string }> {
    return request.post(`/learning/reviews/${reviewId}/disapprove/`)
  },
  
  // 学习资源相关API
  
  // 获取学习资源列表
  getResources(params?: { course?: number; page?: number }): Promise<{ count: number; next: string | null; previous: string | null; results: any[] }> {
    return request.get('/learning/resources/', { params })
  },
  
  // 获取学习资源详情
  getResourceDetail(resourceId: number | string): Promise<any> {
    return request.get(`/learning/resources/${resourceId}/`)
  },
  
  // 创建学习资源
  createResource(data: FormData | Record<string, any>): Promise<any> {
    return request.post('/learning/resources/', data)
  },
  
  // 更新学习资源
  updateResource(resourceId: number | string, data: FormData | Record<string, any>): Promise<any> {
    return request.put(`/learning/resources/${resourceId}/`, data)
  },
  
  // 增加资源下载次数
  incrementResourceDownload(resourceId: number | string): Promise<{ status: string }> {
    return request.post(`/learning/resources/${resourceId}/increment_download/`)
  },
  
  // 分类相关API
  
  // 获取分类列表
  getCategories(): Promise<{ count: number; next: string | null; previous: string | null; results: any[] }> {
    return request.get('/learning/categories/')
  },
  
  // 获取分类详情
  getCategoryDetail(categoryId: number | string): Promise<any> {
    return request.get(`/learning/categories/${categoryId}/`)
  },
  
  // 创建分类
  createCategory(data: { name: string; parent?: number; description?: string; order?: number; is_active?: boolean }): Promise<any> {
    return request.post('/learning/categories/', data)
  },
  
  // 更新分类
  updateCategory(categoryId: number | string, data: { name?: string; parent?: number; description?: string; order?: number; is_active?: boolean }): Promise<any> {
    return request.put(`/learning/categories/${categoryId}/`, data)
  }
}