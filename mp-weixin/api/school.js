import request from './request'

// 院校相关API
const schoolApi = {
  /**
   * 获取院校列表
   * @param {Object} params - 查询参数
   * @param {string} params.search - 搜索关键词
   * @param {string} params.province - 省份
   * @param {string} params.school_type - 院校类型
   * @param {string} params.school_level - 院校层次
   * @param {string} params.sort_by - 排序方式
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @returns {Promise} 院校列表
   */
  getSchools: (params) => {
    return request.get('/schools/', params)
  },

  /**
   * 获取院校详情
   * @param {number} id - 院校ID
   * @returns {Promise} 院校详情
   */
  getSchoolDetail: (id) => {
    return request.get(`/schools/${id}/`)
  },

  /**
   * 获取院校专业
   * @param {number} schoolId - 院校ID
   * @param {Object} params - 查询参数
   * @returns {Promise} 专业列表
   */
  getSchoolMajors: (schoolId, params) => {
    return request.get(`/schools/${schoolId}/majors/`, params)
  },

  /**
   * 获取/创建学校论坛板块
   * @param {number} schoolId - 院校ID
   * @returns {Promise} 论坛板块详情
   */
  getSchoolForum: (schoolId) => {
    return request.get(`/schools/${schoolId}/forums/`)
  },

  /**
   * 获取历年分数线
   * @param {number} schoolId - 院校ID
   * @param {Object} params - 查询参数
   * @param {number} params.year - 年份
   * @param {string} params.province - 省份
   * @param {string} params.score_type - 科类
   * @returns {Promise} 分数线列表
   */
  getSchoolScores: (schoolId, params) => {
    return request.get(`/schools/${schoolId}/admission_scores/`, params)
  },

  /**
   * 收藏院校
   * @param {number} schoolId - 院校ID
   * @returns {Promise} 收藏结果
   */
  favoriteSchool: (schoolId) => {
    return request.post(`/schools/${schoolId}/favorite/`)
  },

  /**
   * 取消收藏院校
   * @param {number} schoolId - 院校ID
   * @returns {Promise} 取消收藏结果
   */
  unfavoriteSchool: (schoolId) => {
    return request.post(`/schools/${schoolId}/unfavorite/`)
  },

  /**
   * 获取我的收藏院校
   * @returns {Promise} 收藏院校列表
   */
  getMyFavorites: () => {
    return request.get('/schools/favorite-schools/')
  },

  /**
   * 院校对比
   * @param {Array} schoolIds - 院校ID列表
   * @returns {Promise} 对比结果
   */
  compareSchools: (schoolIds) => {
    return request.post('/schools/compare/', { school_ids: schoolIds })
  },

  /**
   * 获取省份列表
   * @returns {Promise} 省份列表
   */
  getProvinces: () => {
    return request.get('/schools/provinces/')
  },

  /**
   * 获取学校类型
   * @returns {Promise} 学校类型列表
   */
  getSchoolTypes: () => {
    return request.get('/schools/types/')
  },

  /**
   * 获取学校层次
   * @returns {Promise} 学校层次列表
   */
  getSchoolLevels: () => {
    return request.get('/schools/levels/')
  },

  /**
   * 获取推荐院校
   * @param {Object} params - 查询参数
   * @param {number} params.limit - 数量限制
   * @returns {Promise} 推荐院校列表
   */
  getRecommendations: (params) => {
    return request.get('/schools/recommendations/', params)
  },

  /**
   * 评价学校
   * @param {number} schoolId - 院校ID
   * @param {Object} data - 评价数据
   * @param {number} data.rating - 评分
   * @param {string} data.comment - 评价内容
   * @returns {Promise} 评价结果
   */
  rateSchool: (schoolId, data) => {
    return request.post(`/schools/${schoolId}/rate/`, data)
  }
}

export default schoolApi
