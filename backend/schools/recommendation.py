from django.db.models import Q, Count
from forum.models import Post
from users.models import UserActivity
from core.cache_utils import cached_result, build_cache_key, get_default_timeout
from .models import School, Major
from .serializers import SchoolSerializer, MajorSerializer
from forum.serializers import PostSerializer as ForumPostSerializer


class RecommendationService:
    """推荐服务类"""

    def __init__(self, user):
        self.user = user

    def _cache_key(self, identifier, limit, extra=None):
        parts = ['recommendation', identifier, self.user.id, limit]
        if extra is not None:
            parts.append(extra)
        return build_cache_key(*parts)

    def get_school_recommendations(self, limit=10):
        """获取学校推荐，返回已序列化的推荐结果。"""
        cache_key = self._cache_key('schools', limit)

        def _load():
            recommendations = []
            reasoning = []

            recent_activities = UserActivity.objects.filter(
                user=self.user
            ).order_by('-timestamp')[:100]

            school_ids = set()
            provinces = set()
            school_types = set()
            school_levels = set()

            for activity in recent_activities:
                if activity.target_type == 'school':
                    school_ids.add(activity.target_id)
                elif activity.target_type == 'major':
                    pass

            if school_ids:
                browsed_schools = School.objects.filter(id__in=school_ids)
                provinces.update(browsed_schools.values_list('province', flat=True).distinct())
                school_types.update(browsed_schools.values_list('school_type', flat=True).distinct())
                school_levels.update(browsed_schools.values_list('school_level', flat=True).distinct())

            favorite_schools = self.user.favorite_schools.all()
            if favorite_schools.exists():
                fav_school_types = favorite_schools.values_list('school_type', flat=True).distinct()
                fav_school_levels = favorite_schools.values_list('school_level', flat=True).distinct()

                similar_schools = School.objects.filter(
                    school_type__in=fav_school_types,
                    school_level__in=fav_school_levels
                ).exclude(id__in=school_ids).exclude(id__in=[s.id for s in favorite_schools])

                similar_schools = similar_schools.filter(national_rank__isnull=False).order_by('national_rank')[:limit]

                if similar_schools.exists():
                    recommendations.extend(similar_schools)
                    reasoning.append("基于您收藏的学校类型和层次推荐")

            if len(recommendations) < limit and school_ids:
                province_schools = School.objects.filter(
                    province__in=provinces
                ).exclude(id__in=school_ids).exclude(id__in=[s.id for s in recommendations])

                province_schools = province_schools.filter(national_rank__isnull=False).order_by('national_rank')[:limit - len(recommendations)]

                if province_schools.exists():
                    recommendations.extend(province_schools)
                    reasoning.append("基于您浏览的学校所在省份推荐")

            if len(recommendations) < limit and school_ids:
                major_ids = set()
                for activity in recent_activities:
                    if activity.target_type == 'major':
                        major_ids.add(activity.target_id)

                if major_ids:
                    schools_with_majors = School.objects.filter(
                        schoolmajor__major_id__in=major_ids
                    ).exclude(id__in=school_ids).exclude(id__in=[s.id for s in recommendations])

                    schools_with_majors = schools_with_majors.filter(national_rank__isnull=False).order_by('national_rank')[:limit - len(recommendations)]

                    if schools_with_majors.exists():
                        recommendations.extend(schools_with_majors)
                        reasoning.append("基于您感兴趣的专业推荐")

            if len(recommendations) < limit and (school_types or school_levels):
                type_level_schools = School.objects.filter(
                    Q(school_type__in=school_types) | Q(school_level__in=school_levels)
                ).exclude(id__in=school_ids).exclude(id__in=[s.id for s in recommendations])

                type_level_schools = type_level_schools.filter(national_rank__isnull=False).order_by('national_rank')[:limit - len(recommendations)]

                if type_level_schools.exists():
                    recommendations.extend(type_level_schools)
                    reasoning.append("基于您感兴趣的学校类型和层次推荐")

            if len(recommendations) < limit:
                top_schools = School.objects.filter(
                    national_rank__isnull=False
                ).exclude(id__in=school_ids).exclude(id__in=[s.id for s in recommendations]).order_by('national_rank')[:limit - len(recommendations)]

                if top_schools.exists():
                    recommendations.extend(top_schools)
                    reasoning.append("基于全国排名推荐")

            serializer = SchoolSerializer(recommendations, many=True)
            return {
                'recommendations': serializer.data,
                'reasoning': reasoning,
            }

        return cached_result(
            key=cache_key,
            loader=_load,
            timeout=get_default_timeout('medium'),
            namespace='recommendation',
            compress=True,
        )

    def get_major_recommendations(self, limit=10):
        """获取专业推荐，返回已序列化的推荐结果。"""
        cache_key = self._cache_key('majors', limit)

        def _load():
            recommendations = []
            reasoning = []

            recent_activities = UserActivity.objects.filter(
                user=self.user
            ).order_by('-timestamp')[:100]

            school_ids = set()
            major_ids = set()

            for activity in recent_activities:
                if activity.target_type == 'school':
                    school_ids.add(activity.target_id)
                elif activity.target_type == 'major':
                    major_ids.add(activity.target_id)

            if school_ids:
                schools = School.objects.filter(id__in=school_ids)
                related_majors = Major.objects.filter(
                    schoolmajor__school__in=schools
                ).exclude(id__in=major_ids)

                related_majors = related_majors.annotate(
                    rating_count=Count('ratings')
                ).order_by('-rating_count')[:limit]

                if related_majors.exists():
                    recommendations.extend(related_majors)
                    reasoning.append("基于您浏览的学校推荐相关专业")

            if len(recommendations) < limit and major_ids:
                browsed_majors = Major.objects.filter(id__in=major_ids)
                subject_categories = browsed_majors.values_list('subject_category', flat=True).distinct()

                similar_majors = Major.objects.filter(
                    subject_category__in=subject_categories
                ).exclude(id__in=major_ids).exclude(id__in=[m.id for m in recommendations])

                similar_majors = similar_majors.annotate(
                    rating_count=Count('ratings')
                ).order_by('-rating_count')[:limit - len(recommendations)]

                if similar_majors.exists():
                    recommendations.extend(similar_majors)
                    reasoning.append("基于您浏览的专业推荐相似专业")

            if len(recommendations) < limit:
                hot_majors = Major.objects.exclude(
                    id__in=list(major_ids) + [m.id for m in recommendations]
                ).annotate(
                    rating_count=Count('ratings')
                ).order_by('-rating_count')[:limit - len(recommendations)]

                if hot_majors.exists():
                    recommendations.extend(hot_majors)
                    reasoning.append("推荐热门专业")

            serializer = MajorSerializer(recommendations, many=True)
            return {
                'recommendations': serializer.data,
                'reasoning': reasoning,
            }

        return cached_result(
            key=cache_key,
            loader=_load,
            timeout=get_default_timeout('medium'),
            namespace='recommendation',
            compress=True,
        )

    def get_post_recommendations(self, limit=10, request=None):
        """获取论坛帖子推荐，返回已序列化的推荐结果。"""
        cache_key = self._cache_key('posts', limit)

        def _load():
            recommendations = []
            reasoning = []

            recent_activities = UserActivity.objects.filter(
                user=self.user
            ).order_by('-timestamp')[:100]

            school_ids = set()
            post_ids = set()

            for activity in recent_activities:
                if activity.target_type == 'school':
                    school_ids.add(activity.target_id)
                elif activity.target_type == 'post':
                    post_ids.add(activity.target_id)

            if school_ids:
                related_posts = Post.objects.filter(
                    topic__board__school_id__in=school_ids
                ).exclude(id__in=post_ids).annotate(
                    like_count=Count('likes'),
                    comment_count=Count('comments')
                )

                related_posts = related_posts.order_by('-like_count', '-comment_count')[:limit]

                if related_posts.exists():
                    recommendations.extend(related_posts)
                    reasoning.append("基于您浏览的学校推荐相关帖子")

            if len(recommendations) < limit:
                hot_posts = Post.objects.exclude(
                    id__in=list(post_ids) + [p.id for p in recommendations]
                ).annotate(
                    like_count=Count('likes'),
                    comment_count=Count('comments')
                ).order_by('-like_count', '-comment_count')[:limit - len(recommendations)]

                if hot_posts.exists():
                    recommendations.extend(hot_posts)
                    reasoning.append("推荐热门帖子")

            serializer = ForumPostSerializer(
                recommendations, many=True,
                context={'request': request}
            )
            return {
                'recommendations': serializer.data,
                'reasoning': reasoning,
            }

        return cached_result(
            key=cache_key,
            loader=_load,
            timeout=get_default_timeout('medium'),
            namespace='recommendation',
            compress=True,
        )
