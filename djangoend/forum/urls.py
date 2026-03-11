from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    BoardViewSet,
    TopicViewSet,
    PostViewSet,
    NotificationViewSet,
    BookmarkViewSet,
    TagViewSet,
    forum_stats,
    hot_topics
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'boards', BoardViewSet)
router.register(r'topics', TopicViewSet)
router.register(r'posts', PostViewSet)
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark')
router.register(r'tags', TagViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # 论坛统计数据
    path('stats/', forum_stats, name='forum-stats'),
    
    # 热门话题
    path('hot-topics/', hot_topics, name='hot-topics'),
    
    # 主题相关
    path('boards/<int:board_id>/topics/', TopicViewSet.as_view({'get': 'list', 'post': 'create'}), name='board-topics'),
    path('topics/<int:topic_id>/posts/', PostViewSet.as_view({'get': 'list', 'post': 'create'}), name='topic-posts'),
    
    # 互动相关
    path('posts/<int:post_id>/like/', PostViewSet.as_view({'post': 'like', 'delete': 'unlike'}), name='like-post'),
    path('posts/<int:post_id>/report/', PostViewSet.as_view({'post': 'report'}), name='report-post'),
    path('topics/<int:topic_id>/bookmark/', TopicViewSet.as_view({'post': 'bookmark', 'delete': 'unbookmark'}), name='bookmark-topic'),
    
    # 通知相关
    path('notifications/mark-all-read/', NotificationViewSet.as_view({'post': 'mark_all_read'}), name='mark-all-notifications-read'),
    path('notifications/<int:notification_id>/read/', NotificationViewSet.as_view({'post': 'mark_as_read'}), name='mark-notification-read'),
] 