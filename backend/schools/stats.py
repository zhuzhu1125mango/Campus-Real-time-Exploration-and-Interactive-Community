from django.db.models import Count, Avg, Sum
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from forum.models import Post, Comment
from .models import School, Major, Event, EventRegistration
from users.models import User, UserActivity

class StatsService:
    """统计服务类"""
    
    def __init__(self):
        self.cache_prefix = 'stats_'
    
    def get_school_stats(self):
        """获取学校统计数据"""
        cache_key = f'{self.cache_prefix}school'
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # 总学校数
        total_schools = School.objects.count()
        
        # 学校类型分布
        school_type_distribution = list(School.objects.values('school_type').annotate(count=Count('school_type')))
        
        # 学校层次分布
        school_level_distribution = list(School.objects.values('school_level').annotate(count=Count('school_level')))
        
        # 省份分布
        province_distribution = list(School.objects.values('province').annotate(count=Count('province')).order_by('-count')[:10])
        
        # 平均全国排名
        avg_national_rank = School.objects.filter(national_rank__isnull=False).aggregate(avg_rank=Avg('national_rank'))['avg_rank']
        
        # 学生人数统计
        student_count_stats = School.objects.filter(student_count__isnull=False).aggregate(
            avg_students=Avg('student_count'),
            max_students=Sum('student_count')
        )
        
        result = {
            'total_schools': total_schools,
            'type_distribution': school_type_distribution,
            'level_distribution': school_level_distribution,
            'province_distribution': province_distribution,
            'avg_national_rank': round(avg_national_rank, 1) if avg_national_rank else 0,
            'student_stats': student_count_stats
        }
        
        # 缓存结果，有效期1小时
        cache.set(cache_key, result, 3600)
        
        return result
    
    def get_forum_stats(self):
        """获取论坛统计数据"""
        cache_key = f'{self.cache_prefix}forum'
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # 总帖子数
        total_posts = Post.objects.count()
        
        # 总评论数
        total_comments = Comment.objects.count()
        
        # 帖子状态分布
        post_status_distribution = list(Post.objects.values('content_status').annotate(count=Count('content_status')))
        
        # 最近7天的帖子数量
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_posts = Post.objects.filter(created_at__gte=seven_days_ago).count()
        
        # 最近7天的评论数量
        recent_comments = Comment.objects.filter(created_at__gte=seven_days_ago).count()
        
        result = {
            'total_posts': total_posts,
            'total_comments': total_comments,
            'post_status_distribution': post_status_distribution,
            'recent_posts': recent_posts,
            'recent_comments': recent_comments
        }
        
        # 缓存结果，有效期1小时
        cache.set(cache_key, result, 3600)
        
        return result
    
    def get_event_stats(self):
        """获取活动统计数据"""
        cache_key = f'{self.cache_prefix}event'
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # 总活动数
        total_events = Event.objects.count()
        
        # 活动状态分布
        event_status_distribution = list(Event.objects.values('status').annotate(count=Count('status')))
        
        # 总报名人数
        total_registrations = EventRegistration.objects.count()
        
        # 最近7天的活动数量
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_events = Event.objects.filter(created_at__gte=seven_days_ago).count()
        
        # 最近7天的报名人数
        recent_registrations = EventRegistration.objects.filter(registered_at__gte=seven_days_ago).count()
        
        result = {
            'total_events': total_events,
            'status_distribution': event_status_distribution,
            'total_registrations': total_registrations,
            'recent_events': recent_events,
            'recent_registrations': recent_registrations
        }
        
        # 缓存结果，有效期1小时
        cache.set(cache_key, result, 3600)
        
        return result
    
    def get_user_stats(self):
        """获取用户统计数据"""
        cache_key = f'{self.cache_prefix}user'
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # 总用户数
        total_users = User.objects.count()
        
        # 最近7天的新用户数
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_users = User.objects.filter(date_joined__gte=seven_days_ago).count()
        
        # 用户行为统计
        activity_stats = list(UserActivity.objects.values('activity_type').annotate(count=Count('activity_type')))
        
        # 目标类型统计
        target_stats = list(UserActivity.objects.values('target_type').annotate(count=Count('target_type')))
        
        result = {
            'total_users': total_users,
            'recent_users': recent_users,
            'activity_stats': activity_stats,
            'target_stats': target_stats
        }
        
        # 缓存结果，有效期1小时
        cache.set(cache_key, result, 3600)
        
        return result
    
    def get_dashboard_stats(self):
        """获取仪表盘综合统计数据"""
        cache_key = f'{self.cache_prefix}dashboard'
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        result = {
            'school_stats': self.get_school_stats(),
            'forum_stats': self.get_forum_stats(),
            'event_stats': self.get_event_stats(),
            'user_stats': self.get_user_stats(),
            'last_updated': timezone.now().isoformat()
        }
        
        # 缓存结果，有效期1小时
        cache.set(cache_key, result, 3600)
        
        return result
