from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from forum.models import Topic, Tag as ForumTag
from content.models import Content, Tag as ContentTag
from users.activities import Activity
from users.friendship import Friend
from schools.models import Event, Place


class FeedViewSet(viewsets.ViewSet):
    """统一 Feed 流视图集
    聚合论坛主题、内容文章、用户动态，按不同维度排序返回
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'])
    def feed(self, request):
        """获取统一 Feed 流
        支持 type 参数：
        - recommend: 推荐（综合热度与时间）
        - following: 关注/好友动态
        - nearby: 附近内容（需要 lat/lng）
        """
        feed_type = request.query_params.get('type', 'recommend')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        if feed_type == 'recommend':
            items = self._get_recommend_feed(request)
        elif feed_type == 'following':
            items = self._get_following_feed(request)
        elif feed_type == 'nearby':
            items = self._get_nearby_feed(request)
        else:
            return Response(
                {"detail": "无效的 feed 类型"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 统一按时间倒序排序
        items.sort(key=lambda x: x['created_at'], reverse=True)

        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = items[start:end]

        return Response({
            'results': paginated_items,
            'count': len(items),
            'page': page,
            'page_size': page_size,
            'type': feed_type
        })

    def _serialize_topic(self, topic):
        """将论坛主题序列化为 Feed 项"""
        first_post = topic.posts.filter(is_first_post=True).first()
        author = topic.author
        return {
            'id': f'topic_{topic.id}',
            'object_type': 'topic',
            'object_id': topic.id,
            'title': topic.title,
            'content': first_post.content if first_post else '',
            'author': {
                'id': author.id,
                'username': author.username,
                'avatar': author.avatar.url if author.avatar else None,
            },
            'images': [],
            'meta': {
                'board_name': topic.board.name if topic.board else None,
                'reply_count': max(0, topic.post_count - 1),
                'view_count': topic.views,
            },
            'created_at': topic.created_at,
        }

    def _serialize_content(self, content):
        """将内容文章序列化为 Feed 项"""
        author = content.author
        return {
            'id': f'content_{content.id}',
            'object_type': 'content',
            'object_id': content.id,
            'title': content.title,
            'content': content.summary or content.content[:200],
            'author': {
                'id': author.id,
                'username': author.username,
                'avatar': author.avatar.url if author.avatar else None,
            },
            'images': [content.featured_image.url] if content.featured_image else [],
            'meta': {
                'content_type': content.content_type.name if content.content_type else None,
                'view_count': content.view_count,
                'comment_count': content.comment_count,
                'like_count': content.like_count,
            },
            'created_at': content.publish_date or content.created_at,
        }

    def _serialize_activity(self, activity):
        """将用户动态序列化为 Feed 项"""
        author = activity.user
        return {
            'id': f'activity_{activity.id}',
            'object_type': 'activity',
            'object_id': activity.id,
            'title': activity.target_title or activity.get_activity_type_display(),
            'content': activity.content,
            'author': {
                'id': author.id,
                'username': author.username,
                'avatar': author.avatar.url if author.avatar else None,
            },
            'images': [],
            'meta': {
                'activity_type': activity.activity_type,
                'likes_count': activity.likes_count,
                'comments_count': activity.comments_count,
                'target_url': activity.target_url,
            },
            'created_at': activity.created_at,
        }

    def _get_recommend_feed(self, request):
        """推荐 Feed：综合热度与时间"""
        limit = 50
        since = timezone.now() - timedelta(days=30)

        # 论坛主题：近30天的正常主题
        topics = Topic.objects.filter(
            created_at__gte=since,
            status='normal'
        ).order_by('-created_at')[:limit]

        # 已发布内容
        contents = Content.objects.filter(
            status='published',
            publish_date__gte=since
        ).order_by('-publish_date')[:limit]

        # 公开动态
        activities = Activity.objects.filter(
            is_public=True,
            created_at__gte=since
        ).order_by('-created_at')[:limit]

        items = []
        for topic in topics:
            items.append(self._serialize_topic(topic))
        for content in contents:
            items.append(self._serialize_content(content))
        for activity in activities:
            items.append(self._serialize_activity(activity))

        return items

    def _get_following_feed(self, request):
        """关注 Feed：返回好友/关注用户的动态和发布内容"""
        if not request.user.is_authenticated:
            return []

        friend_ids = Friend.get_friends(request.user)
        friend_ids = [u.id for u in friend_ids]

        if not friend_ids:
            return []

        since = timezone.now() - timedelta(days=30)

        topics = Topic.objects.filter(
            author_id__in=friend_ids,
            created_at__gte=since,
            status='normal'
        ).order_by('-created_at')[:30]

        contents = Content.objects.filter(
            author_id__in=friend_ids,
            status='published',
            publish_date__gte=since
        ).order_by('-publish_date')[:30]

        activities = Activity.objects.filter(
            user_id__in=friend_ids,
            is_public=True,
            created_at__gte=since
        ).order_by('-created_at')[:30]

        items = []
        for topic in topics:
            items.append(self._serialize_topic(topic))
        for content in contents:
            items.append(self._serialize_content(content))
        for activity in activities:
            items.append(self._serialize_activity(activity))

        return items

    def _get_nearby_feed(self, request):
        """附近 Feed：基于地理位置返回活动和地点"""
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = request.query_params.get('radius', '10')

        if lat is None or lng is None:
            return []

        try:
            lat = float(lat)
            lng = float(lng)
            radius_km = max(0.1, min(float(radius), 50))
        except (ValueError, TypeError):
            return []

        from math import degrees, radians, cos

        delta_lat = degrees(radius_km / 6371.0)
        delta_lng = degrees(radius_km / (6371.0 * cos(radians(lat))))

        # 附近学校的活动
        nearby_school_ids = Place.objects.filter(
            is_active=True,
            latitude__gte=lat - delta_lat,
            latitude__lte=lat + delta_lat,
            longitude__gte=lng - delta_lng,
            longitude__lte=lng + delta_lng
        ).values_list('school_id', flat=True).distinct()

        events = Event.objects.filter(
            school_id__in=list(nearby_school_ids),
            status__in=['upcoming', 'ongoing'],
            is_public=True
        ).order_by('start_time')[:20]

        items = []
        for event in events:
            items.append({
                'id': f'event_{event.id}',
                'object_type': 'event',
                'object_id': event.id,
                'title': event.title,
                'content': event.description,
                'author': {
                    'id': event.school.id,
                    'username': event.school.name,
                    'avatar': None,
                },
                'images': [],
                'meta': {
                    'location': event.location,
                    'start_time': event.start_time,
                    'status': event.status,
                },
                'created_at': event.created_at,
            })

        return items

    @action(detail=False, methods=['get'])
    def trending_topics(self, request):
        """获取热门话题/标签"""
        # 论坛标签按关联主题数排序
        forum_tags = ForumTag.objects.annotate(
            topic_count=Count('topics')
        ).filter(topic_count__gt=0).order_by('-topic_count', 'name')[:10]

        # 内容标签按关联内容数排序
        content_tags = ContentTag.objects.annotate(
            content_count=Count('content')
        ).filter(content_count__gt=0).order_by('-content_count', 'name')[:10]

        results = []
        for tag in forum_tags:
            results.append({
                'id': f'forum_tag_{tag.id}',
                'type': 'forum_tag',
                'name': tag.name,
                'description': tag.description,
                'count': tag.topic_count,
            })
        for tag in content_tags:
            results.append({
                'id': f'content_tag_{tag.id}',
                'type': 'content_tag',
                'name': tag.name,
                'description': tag.description,
                'count': tag.content_count,
            })

        # 按数量倒序
        results.sort(key=lambda x: x['count'], reverse=True)
        return Response(results[:15])
