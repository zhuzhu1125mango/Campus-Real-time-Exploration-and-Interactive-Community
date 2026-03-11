from rest_framework import serializers
from .models import (
    Forum, Post, Comment, Tag, School, Major, SchoolMajor, 
    SchoolRating, MajorRating, AdmissionScore
)
from users.serializers import UserSerializer

class SchoolSerializer(serializers.ModelSerializer):
    """学校序列化器"""
    admission_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = School
        fields = [
            'id', 'name', 'english_name', 'code', 'abbreviation', 
            'school_type', 'school_level', 'founded_year', 'province', 
            'city', 'address', 'location', 'website', 'email', 'phone',
            'admission_office_phone', 'admission_office_email', 
            'has_graduate_program', 'introduction', 'features', 'facilities',
            'logo', 'banner', 'student_count', 'faculty_count',
            'national_rank', 'world_rank', 'is_verified',
            'created_at', 'updated_at', 'admission_rate'
        ]
        read_only_fields = ['created_at', 'updated_at', 'admission_rate']
    
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
            'description', 'career_prospects', 'employment_rate', 'avg_salary',
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
            'min_score', 'max_score', 'avg_score', 'created_at', 'updated_at'
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