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
    return request.get(`/posts/${postId}/`)
  },

  getPostComments(postId: number): Promise<{ results: Comment[] }> {
    return request.get(`/posts/${postId}/comments/`)
  },

  // 分类相关
  getCategories(): Promise<Category[]> {
    return request.get('/categories/')
  },

  // 板块相关
  getBoards(): Promise<Board[] | { count: number; next: string | null; previous: string | null; results: Board[] }> {
    return request.get('/boards/')
  },

  getBoard(boardId: number): Promise<Board> {
    return request.get(`/boards/${boardId}/`)
  },

  // 获取板块内活跃主题
  getActiveBoardTopics(boardId: number, days = 7): Promise<{ count: number; next: string | null; previous: string | null; results: Topic[] }> {
    return request.get(`/boards/${boardId}/active_topics/`, { params: { days } })
  },

  // 主题相关
  getTopics(boardId: number, page = 1): Promise<{ count: number; next: string | null; previous: string | null; results: Topic[] }> {
    return request.get(`/boards/${boardId}/topics/`, { params: { page } })
  },

  getTopic(topicId: number): Promise<Topic> {
    return request.get(`/topics/${topicId}/`)
  },

  createTopic(boardId: number, data: { title: string; content: string; tags?: string[] }): Promise<Topic> {
    return request.post(`/boards/${boardId}/topics/`, data)
  },

  // 论坛统计相关
  getForumStats(): Promise<ForumStats> {
    return request.get('/stats/')
  },

  // 热门话题相关
  getHotTopics(days = 7, limit = 10): Promise<Topic[]> {
    return request.get('/hot-topics/', { params: { days, limit } })
  },

  // 通知相关
  getNotifications(): Promise<Notification[]> {
    return request.get('/notifications/')
  },

  markNotificationAsRead(notificationId: number): Promise<void> {
    return request.post(`/notifications/${notificationId}/mark_read/`)
  },

  markAllNotificationsAsRead(): Promise<void> {
    return request.post('/notifications/mark_all_read/')
  },

  // 书签相关
  getBookmarks(): Promise<Bookmark[]> {
    return request.get('/bookmarks/')
  },

  // 获取主题帖子列表
  getTopicPosts(topicId: number, page: number) {
    return request.get<{ results: Post[], count: number }>(
      `/topics/${topicId}/posts/`,
      { params: { page } }
    )
  },

  // 回复主题
  replyTopic(data: { topic: number, content: string }) {
    return request.post<Post>('/posts/', data)
  },

  // 收藏主题
  bookmarkTopic(topicId: number) {
    return request.post(`/topics/${topicId}/bookmark/`)
  },

  // 取消收藏主题
  unbookmarkTopic(topicId: number): Promise<void> {
    return request.post(`/topics/${topicId}/unbookmark/`)
  },

  // 点赞帖子
  likePost(postId: number): Promise<void> {
    return request.post(`/posts/${postId}/like/`)
  },

  // 取消点赞帖子
  unlikePost(postId: number): Promise<void> {
    return request.delete(`/posts/${postId}/unlike/`)
  },

  // 举报帖子
  reportPost(postId: number, reason: string): Promise<void> {
    return request.post(`/posts/${postId}/report/`, { reason })
  },
  
  // 更新帖子
  updatePost(postId: number, data: { content: string }): Promise<Post> {
    return request.patch(`/posts/${postId}/`, data)
  },
  
  // 删除帖子
  deletePost(postId: number): Promise<void> {
    return request.delete(`/posts/${postId}/`)
  },

  // 点赞评论
  likeComment(commentId: number): Promise<void> {
    return request.post(`/comments/${commentId}/like/`)
  },

  // 添加评论
  addComment(data: { post: number; content: string }): Promise<Comment> {
    return request.post('/comments/', data)
  }
} 