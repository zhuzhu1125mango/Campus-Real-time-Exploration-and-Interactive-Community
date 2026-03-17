import request from '@/utils/request'
import type { 
  Post, 
  Comment, 
  Category, 
  Board, 
  Topic, 
  Notification, 
  Bookmark,
  ForumStats
} from '@/types/forum'

export const forumApi = {
  // 帖子相关
  getPost(postId: number): Promise<Post> {
    return request.get(`/api/posts/${postId}/`)
  },

  getPostComments(postId: number): Promise<{ results: Comment[] }> {
    return request.get(`/api/posts/${postId}/comments/`)
  },

  addComment(data: { post: number; content: string; parent?: number }): Promise<Comment> {
    return request.post('/api/comments/', data)
  },

  likePost(postId: number): Promise<void> {
    return request.post(`/api/posts/${postId}/like/`)
  },

  likeComment(commentId: number): Promise<void> {
    return request.post(`/api/comments/${commentId}/like/`)
  },

  // 分类相关
  getCategories(): Promise<Category[]> {
    return request.get('/api/categories/')
  },

  // 板块相关
  getBoards(): Promise<Board[] | { count: number; next: string | null; previous: string | null; results: Board[] }> {
    return request.get('/api/boards/')
  },

  getBoard(boardId: number): Promise<Board> {
    return request.get(`/api/boards/${boardId}/`)
  },

  // 获取板块内活跃主题
  getActiveBoardTopics(boardId: number, days = 7): Promise<{ count: number; next: string | null; previous: string | null; results: Topic[] }> {
    return request.get(`/api/boards/${boardId}/active_topics/`, { params: { days } })
  },

  // 主题相关
  getTopics(boardId: number, page = 1): Promise<{ count: number; next: string | null; previous: string | null; results: Topic[] }> {
    return request.get(`/api/boards/${boardId}/topics/`, { params: { page } })
  },

  getTopic(topicId: number): Promise<Topic> {
    return request.get(`/api/topics/${topicId}/`)
  },

  createTopic(boardId: number, data: { title: string; content: string; tags?: string[] }): Promise<Topic> {
    return request.post(`/api/boards/${boardId}/topics/`, data)
  },

  // 论坛统计相关
  getForumStats(): Promise<ForumStats> {
    return request.get('/api/stats/')
  },

  // 热门话题相关
  getHotTopics(days = 7, limit = 10): Promise<Topic[]> {
    return request.get('/api/hot-topics/', { params: { days, limit } })
  },

  // 通知相关
  getNotifications(): Promise<Notification[]> {
    return request.get('/api/notifications/')
  },

  markNotificationAsRead(notificationId: number): Promise<void> {
    return request.post(`/api/notifications/${notificationId}/read/`)
  },

  markAllNotificationsAsRead(): Promise<void> {
    return request.post('/api/notifications/mark-all-read/')
  },

  // 书签相关
  getBookmarks(): Promise<Bookmark[]> {
    return request.get('/api/bookmarks/')
  },

  addBookmark(topicId: number): Promise<Bookmark> {
    return request.post('/api/bookmarks/', { topic: topicId })
  },

  removeBookmark(bookmarkId: number): Promise<void> {
    return request.delete(`/api/bookmarks/${bookmarkId}/`)
  },

  // 获取主题帖子列表
  getTopicPosts(topicId: number, page: number) {
    return request.get<{ results: Post[], count: number }>(
      `/api/topics/${topicId}/posts/`,
      { params: { page } }
    )
  },

  // 回复主题
  replyTopic(data: { topic: number, content: string }) {
    return request.post<Post>('/api/posts/', data)
  },

  // 收藏主题
  bookmarkTopic(topicId: number) {
    return request.post(`/api/topics/${topicId}/bookmark/`)
  },

  // 取消收藏主题
  unbookmarkTopic(topicId: number): Promise<void> {
    return request.delete(`/api/topics/${topicId}/bookmark/`)
  },

  // 取消点赞帖子
  unlikePost(postId: number): Promise<void> {
    return request.delete(`/api/posts/${postId}/like/`)
  },

  // 举报帖子
  reportPost(postId: number, reason: string): Promise<void> {
    return request.post(`/api/posts/${postId}/report/`, { reason })
  },
  
  // 更新帖子
  updatePost(postId: number, data: { content: string }): Promise<Post> {
    return request.patch(`/api/posts/${postId}/`, data)
  },
  
  // 删除帖子
  deletePost(postId: number): Promise<void> {
    return request.delete(`/api/posts/${postId}/`)
  }
} 