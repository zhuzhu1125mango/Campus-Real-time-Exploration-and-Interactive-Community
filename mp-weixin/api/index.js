// API 模块索引
import request from './request'
import userApi from './user'
import schoolApi from './school'
import forumApi from './forum'
import chatApi from './chat'
import contentApi from './content'
import learningApi from './learning'
import notificationApi from './notification'

export {
  request,
  userApi,
  schoolApi,
  forumApi,
  chatApi,
  contentApi,
  learningApi,
  notificationApi
}

export default {
  request,
  user: userApi,
  school: schoolApi,
  forum: forumApi,
  chat: chatApi,
  content: contentApi,
  learning: learningApi,
  notification: notificationApi
}
