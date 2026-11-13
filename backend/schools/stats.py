from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from forum.models import Post, Comment
from core.cache_utils import cached_result, build_cache_key, get_default_timeout
from .models import School, Event, EventRegistration
from users.models import User, UserActivity


class StatsService:
    """统计服务类"""

    @staticmethod
    def _cache_key(identifier):
        return build_cache_key('stats', identifier)

    def get_school_stats(self):
        """获取学校统计数据"""
        def _load():
            total_schools = School.objects.count()
            school_type_distribution = list(School.objects.values('school_type').annotate(count=Count('school_type')))
            school_level_distribution = list(School.objects.values('school_level').annotate(count=Count('school_level')))
            province_distribution = list(School.objects.values('province').annotate(count=Count('province')).order_by('-count')[:10])
            avg_national_rank = School.objects.filter(national_rank__isnull=False).aggregate(avg_rank=Avg('national_rank'))['avg_rank']
            student_count_stats = School.objects.filter(student_count__isnull=False).aggregate(
                avg_students=Avg('student_count'),
                max_students=Sum('student_count')
            )

            return {
                'total_schools': total_schools,
                'type_distribution': school_type_distribution,
                'level_distribution': school_level_distribution,
                'province_distribution': province_distribution,
                'avg_national_rank': round(avg_national_rank, 1) if avg_national_rank else 0,
                'student_stats': student_count_stats
            }

        return cached_result(
            key=self._cache_key('school'),
            loader=_load,
            timeout=get_default_timeout('hot'),
            namespace='stats',
            compress=True,
        )

    def get_forum_stats(self):
        """获取论坛统计数据"""
        def _load():
            total_posts = Post.objects.count()
            total_comments = Comment.objects.count()
            post_status_distribution = list(Post.objects.values('content_status').annotate(count=Count('content_status')))
            seven_days_ago = timezone.now() - timedelta(days=7)
            recent_posts = Post.objects.filter(created_at__gte=seven_days_ago).count()
            recent_comments = Comment.objects.filter(created_at__gte=seven_days_ago).count()

            return {
                'total_posts': total_posts,
                'total_comments': total_comments,
                'post_status_distribution': post_status_distribution,
                'recent_posts': recent_posts,
                'recent_comments': recent_comments
            }

        return cached_result(
            key=self._cache_key('forum'),
            loader=_load,
            timeout=get_default_timeout('hot'),
            namespace='stats',
            compress=True,
        )

    def get_event_stats(self):
        """获取活动统计数据"""
        def _load():
            total_events = Event.objects.count()
            event_status_distribution = list(Event.objects.values('status').annotate(count=Count('status')))
            total_registrations = EventRegistration.objects.count()
            seven_days_ago = timezone.now() - timedelta(days=7)
            recent_events = Event.objects.filter(created_at__gte=seven_days_ago).count()
            recent_registrations = EventRegistration.objects.filter(registered_at__gte=seven_days_ago).count()

            return {
                'total_events': total_events,
                'status_distribution': event_status_distribution,
                'total_registrations': total_registrations,
                'recent_events': recent_events,
                'recent_registrations': recent_registrations
            }

        return cached_result(
            key=self._cache_key('event'),
            loader=_load,
            timeout=get_default_timeout('hot'),
            namespace='stats',
            compress=True,
        )

    def get_user_stats(self):
        """获取用户统计数据"""
        def _load():
            total_users = User.objects.count()
            seven_days_ago = timezone.now() - timedelta(days=7)
            recent_users = User.objects.filter(date_joined__gte=seven_days_ago).count()
            activity_stats = list(UserActivity.objects.values('activity_type').annotate(count=Count('activity_type')))
            target_stats = list(UserActivity.objects.values('target_type').annotate(count=Count('target_type')))

            return {
                'total_users': total_users,
                'recent_users': recent_users,
                'activity_stats': activity_stats,
                'target_stats': target_stats
            }

        return cached_result(
            key=self._cache_key('user'),
            loader=_load,
            timeout=get_default_timeout('hot'),
            namespace='stats',
            compress=True,
        )

    def get_dashboard_stats(self):
        """获取仪表盘综合统计数据"""
        def _load():
            return {
                'school_stats': self.get_school_stats(),
                'forum_stats': self.get_forum_stats(),
                'event_stats': self.get_event_stats(),
                'user_stats': self.get_user_stats(),
                'last_updated': timezone.now().isoformat()
            }

        return cached_result(
            key=self._cache_key('dashboard'),
            loader=_load,
            timeout=get_default_timeout('hot'),
            namespace='stats',
            compress=True,
        )
