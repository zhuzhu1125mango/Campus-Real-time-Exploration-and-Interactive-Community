/**
 * 双端共享的 API 端点常量
 * 用于避免 H5 与小程序中硬编码重复的路径。
 */

export const API_ENDPOINTS = {
  // 健康检查
  HEALTH: '/health/',

  // 认证
  TOKEN_REFRESH: '/token/refresh/',

  // 用户
  USERS: '/users/users/',
  USER_ME: '/users/users/me/',
  USER_LOGIN: '/users/users/login/',
  USER_EMAIL_LOGIN: '/users/users/email_code_login/',
  USER_PHONE_LOGIN: '/users/users/phone_code_login/',
  USER_REGISTER: '/users/users/',
  USER_RESET_PASSWORD: '/users/reset-password/',
  USER_CHANGE_PASSWORD: '/users/users/change_password/',
  USER_FORGOT_PASSWORD: '/users/users/forgot_password/',
  USER_PROFILE_STATS: (userId) => `/users/users/${userId}/profile_stats/`,
  USER_TOPICS: (userId) => `/users/users/${userId}/topics/`,
  USER_POSTS: (userId) => `/users/users/${userId}/posts/`,
  USER_FOLLOW: (userId) => `/users/users/${userId}/follow/`,
  USER_UNFOLLOW: (userId) => `/users/users/${userId}/unfollow/`,
  USER_POINTS: (userId) => `/users/users/${userId}/points/`,
  USER_POINTS_RECORDS: (userId) => `/users/users/${userId}/points_records/`,
  USER_DAILY_CHECKIN: '/users/users/daily_checkin/',
  USER_LOGOUT: '/users/users/logout/',

  // 验证码
  EMAIL_CODE: '/users/email-code/',
  PHONE_CODE: '/users/phone-code/',

  // 收藏
  FAVORITES_BY_CATEGORY: '/users/favorites/by_category/',
  FAVORITES_ADD: '/users/favorites/add_favorite/',
  FAVORITES_REMOVE: '/users/favorites/remove_favorite/',

  // 通知
  NOTIFICATIONS: '/users/notifications/',
  NOTIFICATIONS_COUNT: '/users/notifications/count/',
  NOTIFICATIONS_MARK_ALL_READ: '/users/notifications/mark_all_read/',
  NOTIFICATIONS_DELETE_ALL_READ: '/users/notifications/delete_all_read/',
  NOTIFICATIONS_TYPE_COUNTS: '/users/notifications/type_counts/',
  NOTIFICATION_MARK_READ: (id) => `/users/notifications/${id}/mark_read/`,
  NOTIFICATION_DELETE: (id) => `/users/notifications/${id}/`,

  // 好友
  FRIENDS_LIST: '/users/friends/friend_list/',
  FRIENDS_REMOVE: '/users/friends/remove/',
  FRIENDS_CHECK: '/users/friends/check/',
  FRIEND_REQUESTS: '/users/friend-requests/',
  FRIEND_REQUESTS_RECEIVED: '/users/friend-requests/received/',
  FRIEND_REQUESTS_SENT: '/users/friend-requests/sent/',
  FRIEND_REQUEST_ACCEPT: (id) => `/users/friend-requests/${id}/accept/`,
  FRIEND_REQUEST_REJECT: (id) => `/users/friend-requests/${id}/reject/`,

  // 私信
  MESSAGES_CONVERSATIONS: '/users/messages/conversations/',
  MESSAGES_CONVERSATION: '/users/messages/conversation/',
  MESSAGES_UNREAD_COUNT: '/users/messages/unread_count/',
  MESSAGES_MARK_ALL_READ: '/users/messages/mark_all_read/',
  MESSAGES_BY_USER: (userId) => `/users/messages/${userId}/`,
  MESSAGE_SEND: (userId) => `/users/messages/${userId}/`,
  MESSAGE_MARK_READ: (id) => `/users/messages/${id}/mark_read/`,
  MESSAGES_MARK_READ_BY_USER: (userId) => `/users/messages/${userId}/mark_read/`,

  // 动态
  ACTIVITIES: '/users/activities/',
  ACTIVITY_FEED: '/users/activities/feed/',
  ACTIVITY_MY: '/users/activities/my_activities/',
  ACTIVITY_DETAIL: (id) => `/users/activities/${id}/`,
  ACTIVITY_COMMENTS: (id) => `/users/activities/${id}/comments/`,
  ACTIVITY_LIKE: (id) => `/users/activities/${id}/like/`,
  ACTIVITY_UNLIKE: (id) => `/users/activities/${id}/unlike/`,
  ACTIVITY_COMMENTS_CREATE: '/users/activity-comments/',

  // 积分
  POINTS_LEADERBOARD: '/users/points-leaderboard/',

  // 论坛
  FORUM_CATEGORIES: '/categories/',
  FORUM_BOARDS: '/boards/',
  FORUM_BOARD: (id) => `/boards/${id}/`,
  FORUM_BOARD_ACTIVE_TOPICS: (id) => `/boards/${id}/active_topics/`,
  FORUM_TOPICS: '/topics/',
  FORUM_TOPIC: (id) => `/topics/${id}/`,
  FORUM_TOPIC_POSTS: (id) => `/topics/${id}/posts/`,
  FORUM_TOPIC_BOOKMARK: (id) => `/topics/${id}/bookmark/`,
  FORUM_POSTS: '/posts/',
  FORUM_POST: (id) => `/posts/${id}/`,
  FORUM_POST_LIKE: (id) => `/posts/${id}/like/`,
  FORUM_POST_REPORT: (id) => `/posts/${id}/report/`,
  FORUM_COMMENTS: '/comments/',
  FORUM_COMMENT_LIKE: (id) => `/comments/${id}/like/`,
  FORUM_COMMENT_REPORT: (id) => `/comments/${id}/report/`,
  FORUM_BOOKMARKS: '/bookmarks/',
  FORUM_NOTIFICATIONS: '/notifications/',
  FORUM_STATS: '/stats/',
  FORUM_HOT_TOPICS: '/hot-topics/',
  FORUM_TAGS_HOT: '/tags/hot/',
  FORUM_TAG: (id) => `/tags/${id}/`,
  FORUM_TAG_TOPICS: (id) => `/tags/${id}/topics/`,

  // 院校
  SCHOOLS: '/schools/schools/',
  SCHOOL: (id) => `/schools/schools/${id}/`,
  SCHOOL_FILTERS: '/schools/schools/filters/',
  SCHOOL_COMPARE: '/schools/schools/compare/',
  SCHOOL_RATINGS: (id) => `/schools/schools/${id}/ratings/`,
  SCHOOL_EVENTS: (id) => `/schools/schools/${id}/events/`,
  SCHOOL_PLACES: (id) => `/schools/schools/${id}/places/`,
  SCHOOL_PLACES_NEARBY: '/schools/places/nearby/',
  SCHOOL_CHECKIN: '/schools/checkin/',
  SCHOOL_RECOMMENDATIONS: '/schools/recommendations/',

  // 在线学习
  LEARNING_COURSES: '/learning/courses/',
  LEARNING_COURSE: (id) => `/learning/courses/${id}/`,
  LEARNING_COURSE_ENROLL: (id) => `/learning/courses/${id}/enroll/`,
  LEARNING_COURSE_REVIEWS: (id) => `/learning/courses/${id}/reviews/`,
  LEARNING_MY_COURSES: '/learning/my-courses/',
  LEARNING_MY_PROGRESS: '/learning/my-progress/',
  LEARNING_LESSON: (id) => `/learning/lessons/${id}/`,
  LEARNING_LESSON_COMPLETE: (id) => `/learning/lessons/${id}/complete/`,
  LEARNING_RESOURCES: '/learning/resources/',

  // 内容中心
  CONTENT_TYPES: '/content/content-types/',
  CONTENT_CATEGORIES: '/content/categories/',
  CONTENT_ITEMS: '/content/contents/',
  CONTENT_ITEM: (id) => `/content/contents/${id}/`,
  CONTENT_ITEM_COMMENTS: (id) => `/content/contents/${id}/comments/`,
  CONTENT_ITEM_LIKE: (id) => `/content/contents/${id}/like/`,

  // Feed
  FEED: '/feed/',
  TRENDING_TOPICS: '/feed/trending/',

  // 搜索
  SEARCH: '/search/',

  // 公共聊天室
  CHAT_RECENT_MESSAGES: '/chat/messages/recent_messages/',
  CHAT_ONLINE_USERS: '/chat/messages/online_users/',
  CHAT_SEND_MESSAGE: '/chat/send_message/'
}
