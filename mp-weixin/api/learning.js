// 在线学习 API 模块
import request from './request'

const learningApi = {
  // 课程列表
  getCourses(params = {}) {
    return request.get('/learning/courses/', params)
  },

  // 课程详情
  getCourseDetail(courseId) {
    return request.get(`/learning/courses/${courseId}/`)
  },

  // 课程章节
  getCourseChapters(courseId) {
    return request.get(`/learning/courses/${courseId}/chapters/`)
  },

  // 课程课时
  getCourseLessons(courseId) {
    return request.get(`/learning/courses/${courseId}/lessons/`)
  },

  // 课程资源
  getCourseResources(courseId) {
    return request.get(`/learning/courses/${courseId}/resources/`)
  },

  // 课程评价
  getCourseReviews(courseId) {
    return request.get(`/learning/courses/${courseId}/reviews/`)
  },

  // 课时详情
  getLessonDetail(lessonId) {
    return request.get(`/learning/lessons/${lessonId}/`)
  },

  // 增加课时观看次数
  incrementLessonView(lessonId) {
    return request.post(`/learning/lessons/${lessonId}/increment_view/`)
  },

  // 报名列表
  getEnrollments(params = {}) {
    return request.get('/learning/enrollments/', params)
  },

  // 报名课程
  enrollCourse(courseId) {
    return request.post('/learning/enrollments/', { course: courseId })
  },

  // 完成课程
  completeCourse(enrollmentId) {
    return request.post(`/learning/enrollments/${enrollmentId}/complete/`)
  },

  // 进度列表
  getProgresses(params = {}) {
    return request.get('/learning/progresses/', params)
  },

  // 记录课时学习进度（创建或更新）
  recordProgress(data) {
    return request.post('/learning/progresses/record/', data)
  },

  // 创建/更新进度
  updateProgress(progressId, data) {
    return request.put(`/learning/progresses/${progressId}/`, data)
  },

  // 创建评价
  createReview(data) {
    return request.post('/learning/reviews/', data)
  },

  // 学习资源列表
  getResources(params = {}) {
    return request.get('/learning/resources/', params)
  },

  // 资源详情
  getResourceDetail(resourceId) {
    return request.get(`/learning/resources/${resourceId}/`)
  },

  // 增加资源下载次数
  incrementResourceDownload(resourceId) {
    return request.post(`/learning/resources/${resourceId}/increment_download/`)
  },

  // 分类列表
  getCategories() {
    return request.get('/learning/categories/')
  }
}

export default learningApi
