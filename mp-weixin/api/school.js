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
  },

  /**
   * 获取附近地点
   * @param {Object} params - 查询参数
   * @param {number} params.lat - 纬度
   * @param {number} params.lng - 经度
   * @param {number} [params.radius] - 半径（km）
   * @param {string} [params.category] - 地点分类
   * @returns {Promise} 地点列表
   */
  getNearbyPlaces: (params) => {
    return request.get('/schools/explore/nearby_places/', params)
  },

  /**
   * 获取附近活动
   * @param {Object} params - 查询参数
   * @param {number} params.lat - 纬度
   * @param {number} params.lng - 经度
   * @param {number} [params.radius] - 半径（km）
   * @param {number} [params.school_id] - 学校ID
   * @returns {Promise} 活动列表
   */
  getNearbyEvents: (params) => {
    return request.get('/schools/explore/nearby_events/', params)
  },

  /**
   * 获取地点列表
   * @param {Object} params - 查询参数
   * @param {number} [params.school_id] - 学校ID
   * @param {string} [params.category] - 地点分类
   * @returns {Promise} 地点列表
   */
  getPlaces: (params) => {
    return request.get('/schools/explore/places/', params)
  },

  /**
   * 地点打卡
   * @param {number} placeId - 地点ID
   * @param {Object} data - 打卡数据
   * @param {number} [data.latitude] - 纬度
   * @param {number} [data.longitude] - 经度
   * @param {string} [data.note] - 备注
   * @returns {Promise} 打卡结果
   */
  checkIn: (placeId, data) => {
    return request.post('/schools/explore/checkin/', {
      place_id: placeId,
      ...data
    })
  },

  /**
   * 获取我的打卡记录
   * @returns {Promise} 打卡记录列表
   */
  getMyCheckIns: () => {
    return request.get('/schools/explore/my_checkins/')
  }
}

export default schoolApi
