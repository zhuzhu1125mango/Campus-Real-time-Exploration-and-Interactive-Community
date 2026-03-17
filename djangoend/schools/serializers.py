from rest_framework import serializers
import random
from .models import (
    Forum, Post, Comment, Tag, School, Major, SchoolMajor, 
    SchoolRating, MajorRating, AdmissionScore, Event, EventRegistration
)
from users.serializers import UserSerializer

class SchoolSerializer(serializers.ModelSerializer):
    """学校序列化器"""
    admission_rate = serializers.SerializerMethodField()
    majors = serializers.SerializerMethodField()
    admission_scores = serializers.SerializerMethodField()
    
    class Meta:
        model = School
        fields = [
            'id', 'name', 'english_name', 'code', 'abbreviation', 
            'school_type', 'school_level', 'founded_year', 'province', 
            'city', 'address', 'website', 'description',
            'student_count', 'faculty_count', 'campus_area',
            'national_rank', 'created_at', 'updated_at', 'admission_rate',
            'majors', 'admission_scores'
        ]
        read_only_fields = ['created_at', 'updated_at', 'admission_rate', 'majors', 'admission_scores']
    
    def get_majors(self, obj):
        """获取学校的专业列表"""
        school_majors = obj.majors.filter(is_active=True)
        majors = []
        for sm in school_majors:
            majors.append({
                'id': sm.major.id,
                'name': sm.major.name,
                'code': sm.major.code,
                'description': sm.major.description,
                'employment_rate': round(random.uniform(75, 98), 1),
                'avg_salary': int(random.uniform(5000, 15000))
            })
        return majors
    
    def get_admission_scores(self, obj):
        """获取学校的录取分数线"""
        scores = obj.admission_scores.all()
        score_list = []
        for score in scores:
            score_list.append({
                'id': score.id,
                'year': score.year,
                'province': score.province,
                'science': score.min_score if score.score_type == 'science' else None,
                'arts': score.min_score if score.score_type == 'arts' else None
            })
        return score_list
    
    def get_admission_rate(self, obj):
        """
        计算学校的录取率（如果有相关信息）
        暂时返回随机值作为示例
        """
        import random
        # 在实际应用中，应该根据实际数据计算
        # 例如：成功录取人数 / 申请总人数
        return round(random.uniform(5, 40), 1)  # 返回5%到40%之间的随机值

class MajorSerializer(serializers.ModelSerializer):
    """专业序列化器"""
    employment_rate = serializers.SerializerMethodField()
    avg_salary = serializers.SerializerMethodField()
    
    class Meta:
        model = Major
        fields = [
            'id', 'name', 'code', 'degree_type', 'subject_category',
            'description', 'employment_rate', 'avg_salary',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'employment_rate', 'avg_salary']
    
    def get_employment_rate(self, obj):
        """获取专业就业率"""
        import random
        # 实际应用中应从数据统计计算
        return round(random.uniform(75, 98), 1)  # 返回75%-98%之间的随机值
    
    def get_avg_salary(self, obj):
        """获取专业平均薪资"""
        import random
        # 实际应用中应从数据统计计算
        return int(random.uniform(5000, 15000))  # 返回5000-15000之间的随机值

class SchoolMajorSerializer(serializers.ModelSerializer):
    """学校专业关联序列化器"""
    major = MajorSerializer(read_only=True)
    
    class Meta:
        model = SchoolMajor
        fields = ['id', 'school', 'major', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class AdmissionScoreSerializer(serializers.ModelSerializer):
    """录取分数线序列化器"""
    class Meta:
        model = AdmissionScore
        fields = [
            'id', 'school', 'major', 'year', 'province', 'score_type',
            'min_score', 'avg_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class SchoolRatingSerializer(serializers.ModelSerializer):
    """学校评分序列化器"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = SchoolRating
        fields = ['id', 'school', 'user', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

class MajorRatingSerializer(serializers.ModelSerializer):
    """专业评分序列化器"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MajorRating
        fields = ['id', 'major', 'user', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'description']

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'parent', 'likes_count', 'created_at', 'updated_at']
        read_only_fields = ['author', 'created_at', 'updated_at']
    
    def get_likes_count(self, obj):
        return obj.likes.count()

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Post
        fields = ['id', 'forum', 'author', 'title', 'content', 'status', 
                 'views', 'likes_count', 'comments_count', 'tags', 
                 'created_at', 'updated_at']
        read_only_fields = ['author', 'views', 'created_at', 'updated_at']
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
    def get_likes_count(self, obj):
        return obj.likes.count()

class ForumSerializer(serializers.ModelSerializer):
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Forum
        fields = ['id', 'school', 'name', 'description', 'posts_count', 
                 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_posts_count(self, obj):
        return obj.posts.count()

class EventSerializer(serializers.ModelSerializer):
    """校园活动序列化器"""
    school = serializers.StringRelatedField()
    registration_count = serializers.SerializerMethodField()
    is_registered = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'school', 'start_time', 'end_time',
            'location', 'organizer', 'capacity', 'registration_deadline',
            'is_public', 'status', 'registration_count', 'is_registered',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'registration_count', 'is_registered']
    
    def get_registration_count(self, obj):
        """获取活动报名人数"""
        return obj.registrations.count()
    
    def get_is_registered(self, obj):
        """检查当前用户是否已报名"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.registrations.filter(user=request.user).exists()
        return False

class EventRegistrationSerializer(serializers.ModelSerializer):
    """活动报名序列化器"""
    event = EventSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = EventRegistration
        fields = [
            'id', 'event', 'user', 'status', 'metadata',
            'registered_at', 'updated_at'
        ]
        read_only_fields = ['user', 'registered_at', 'updated_at']
