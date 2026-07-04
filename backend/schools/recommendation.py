from django.db.models import Q, Count, Avg
from django.core.cache import cache
from users.models import UserActivity
from .models import School, Major, Post

class RecommendationService:
    """推荐服务类"""
    
    def __init__(self, user):
        self.user = user
        self.cache_prefix = f'recommendation_{user.id}_'
    
    def get_school_recommendations(self, limit=10):
        """获取学校推荐"""
        cache_key = f'{self.cache_prefix}schools_{limit}'
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        recommendations = []
        reasoning = []
        
        # 获取用户最近的行为记录
        recent_activities = UserActivity.objects.filter(
            user=self.user
        ).order_by('-timestamp')[:100]  # 取更多记录以获得更准确的推荐
        
        # 分析用户行为，提取兴趣点
        school_ids = set()
        major_ids = set()
        provinces = set()
        school_types = set()
        school_levels = set()
        
        for activity in recent_activities:
            if activity.target_type == 'school':
                school_ids.add(activity.target_id)
            elif activity.target_type == 'major':
                major_ids.add(activity.target_id)
        
        # 分析浏览过的学校的特征
        if school_ids:
            browsed_schools = School.objects.filter(id__in=school_ids)
            provinces.update(browsed_schools.values_list('province', flat=True).distinct())
            school_types.update(browsed_schools.values_list('school_type', flat=True).distinct())
            school_levels.update(browsed_schools.values_list('school_level', flat=True).distinct())
        
        # 1. 基于用户收藏的学校推荐
        favorite_schools = self.user.favorite_schools.all()
        if favorite_schools.exists():
            # 提取收藏学校的特征
            fav_school_types = favorite_schools.values_list('school_type', flat=True).distinct()
            fav_school_levels = favorite_schools.values_list('school_level', flat=True).distinct()
            fav_provinces = favorite_schools.values_list('province', flat=True).distinct()
            
            # 推荐相同类型和层次的学校
            similar_schools = School.objects.filter(
                school_type__in=fav_school_types,
                school_level__in=fav_school_levels
            ).exclude(id__in=school_ids).exclude(id__in=[s.id for s in favorite_schools])
            
            # 按全国排名排序
            similar_schools = similar_schools.filter(national_rank__isnull=False).order_by('national_rank')[:limit]
            
            if similar_schools.exists():
                recommendations.extend(similar_schools)
                reasoning.append("基于您收藏的学校类型和层次推荐")
        
        # 2. 基于浏览历史推荐
        if len(recommendations) < limit and school_ids:
            # 推荐相同省份的学校
            province_schools = School.objects.filter(
                province__in=provinces
            ).exclude(id__in=school_ids).exclude(id__in=[s.id for s in recommendations])
            
            # 按全国排名排序
            province_schools = province_schools.filter(national_rank__isnull=False).order_by('national_rank')[:limit - len(recommendations)]
            
            if province_schools.exists():
                recommendations.extend(province_schools)
                reasoning.append("基于您浏览的学校所在省份推荐")
        
        # 3. 基于专业兴趣推荐
        if len(recommendations) < limit and major_ids:
            # 查找开设用户感兴趣专业的学校
            schools_with_majors = School.objects.filter(
                schoolmajor__major_id__in=major_ids
            ).exclude(id__in=school_ids).exclude(id__in=[s.id for s in recommendations])
            
            # 按全国排名排序
            schools_with_majors = schools_with_majors.filter(national_rank__isnull=False).order_by('national_rank')[:limit - len(recommendations)]
            
            if schools_with_majors.exists():
                recommendations.extend(schools_with_majors)
                reasoning.append("基于您感兴趣的专业推荐")
        
        # 4. 基于学校类型和层次推荐
        if len(recommendations) < limit and (school_types or school_levels):
            type_level_schools = School.objects.filter(
                Q(school_type__in=school_types) | Q(school_level__in=school_levels)
            ).exclude(id__in=school_ids).exclude(id__in=[s.id for s in recommendations])
            
            # 按全国排名排序
            type_level_schools = type_level_schools.filter(national_rank__isnull=False).order_by('national_rank')[:limit - len(recommendations)]
            
            if type_level_schools.exists():
                recommendations.extend(type_level_schools)
                reasoning.append("基于您感兴趣的学校类型和层次推荐")
        
        # 5. 如果推荐数量仍然不足，推荐全国排名靠前的学校
        if len(recommendations) < limit:
            top_schools = School.objects.filter(
                national_rank__isnull=False
            ).exclude(id__in=school_ids).exclude(id__in=[s.id for s in recommendations]).order_by('national_rank')[:limit - len(recommendations)]
            
            if top_schools.exists():
                recommendations.extend(top_schools)
                reasoning.append("基于全国排名推荐")
        
        # 缓存结果，有效期30分钟
        result = {'schools': recommendations, 'reasoning': reasoning}
        cache.set(cache_key, result, 1800)
        
        return result
    
    def get_major_recommendations(self, limit=10):
        """获取专业推荐"""
        cache_key = f'{self.cache_prefix}majors_{limit}'
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        recommendations = []
        reasoning = []
        
        # 获取用户最近的行为记录
        recent_activities = UserActivity.objects.filter(
            user=self.user
        ).order_by('-timestamp')[:100]
        
        # 分析用户行为，提取兴趣点
        school_ids = set()
        major_ids = set()
        
        for activity in recent_activities:
            if activity.target_type == 'school':
                school_ids.add(activity.target_id)
            elif activity.target_type == 'major':
                major_ids.add(activity.target_id)
        
        # 1. 基于用户浏览的学校推荐相关专业
        if school_ids:
            # 获取这些学校开设的专业
            schools = School.objects.filter(id__in=school_ids)
            related_majors = Major.objects.filter(
                schoolmajor__school__in=schools
            ).exclude(id__in=major_ids)
            
            # 按专业热度排序（基于评价数量）
            related_majors = related_majors.annotate(
                rating_count=Count('ratings')
            ).order_by('-rating_count')[:limit]
            
            if related_majors.exists():
                recommendations.extend(related_majors)
                reasoning.append("基于您浏览的学校推荐相关专业")
        
        # 2. 基于用户浏览的专业推荐相似专业
        if len(recommendations) < limit and major_ids:
            # 获取用户浏览过的专业
            browsed_majors = Major.objects.filter(id__in=major_ids)
            # 提取专业的学科门类
            subject_categories = browsed_majors.values_list('subject_category', flat=True).distinct()
            
            # 推荐相同学科门类的专业
            similar_majors = Major.objects.filter(
                subject_category__in=subject_categories
            ).exclude(id__in=major_ids).exclude(id__in=[m.id for m in recommendations])
            
            # 按专业热度排序
            similar_majors = similar_majors.annotate(
                rating_count=Count('ratings')
            ).order_by('-rating_count')[:limit - len(recommendations)]
            
            if similar_majors.exists():
                recommendations.extend(similar_majors)
                reasoning.append("基于您浏览的专业推荐相似专业")
        
        # 3. 推荐热门专业
        if len(recommendations) < limit:
            hot_majors = Major.objects.filter(
                id__not_in=major_ids + [m.id for m in recommendations]
            ).annotate(
                rating_count=Count('ratings')
            ).order_by('-rating_count')[:limit - len(recommendations)]
            
            if hot_majors.exists():
                recommendations.extend(hot_majors)
                reasoning.append("推荐热门专业")
        
        # 缓存结果，有效期30分钟
        result = {'majors': recommendations, 'reasoning': reasoning}
        cache.set(cache_key, result, 1800)
        
        return result
    
    def get_post_recommendations(self, limit=10):
        """获取论坛帖子推荐"""
        cache_key = f'{self.cache_prefix}posts_{limit}'
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        recommendations = []
        reasoning = []
        
        # 获取用户最近的行为记录
        recent_activities = UserActivity.objects.filter(
            user=self.user
        ).order_by('-timestamp')[:100]
        
        # 分析用户行为，提取兴趣点
        school_ids = set()
        post_ids = set()
        
        for activity in recent_activities:
            if activity.target_type == 'school':
                school_ids.add(activity.target_id)
            elif activity.target_type == 'post':
                post_ids.add(activity.target_id)
        
        # 1. 基于用户浏览的学校推荐相关帖子
        if school_ids:
            # 获取这些学校论坛的帖子
            related_posts = Post.objects.filter(
                forum__school_id__in=school_ids
            ).exclude(id__in=post_ids)
            
            # 按帖子热度排序（基于点赞和评论数）
            related_posts = related_posts.order_by('-like_count', '-comment_count')[:limit]
            
            if related_posts.exists():
                recommendations.extend(related_posts)
                reasoning.append("基于您浏览的学校推荐相关帖子")
        
        # 2. 推荐热门帖子
        if len(recommendations) < limit:
            hot_posts = Post.objects.filter(
                id__not_in=post_ids + [p.id for p in recommendations]
            ).order_by('-like_count', '-comment_count')[:limit - len(recommendations)]
            
            if hot_posts.exists():
                recommendations.extend(hot_posts)
                reasoning.append("推荐热门帖子")
        
        # 缓存结果，有效期30分钟
        result = {'posts': recommendations, 'reasoning': reasoning}
        cache.set(cache_key, result, 1800)
        
        return result
