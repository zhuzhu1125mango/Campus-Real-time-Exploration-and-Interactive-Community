from rest_framework import serializers
from .activities import Activity, ActivityLike, ActivityComment
from .serializers import UserSerializer


class ActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Activity
        fields = [
            'id', 'user', 'activity_type', 'content', 'target_content_type',
            'target_object_id', 'target_title', 'target_url', 'is_public',
            'likes_count', 'comments_count', 'is_liked', 'created_at'
        ]
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class ActivityCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ['activity_type', 'content', 'target_content_type', 'target_object_id', 'target_title', 'target_url', 'is_public']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ActivityLikeSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    activity = serializers.CharField(source='activity.id')
    
    class Meta:
        model = ActivityLike
        fields = ['id', 'user', 'activity', 'created_at']


class ActivityLikeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLike
        fields = ['activity']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        # 检查是否已经点赞
        activity = validated_data['activity']
        if activity.likes.filter(user=validated_data['user']).exists():
            raise serializers.ValidationError('已经点过赞了')
        # 创建点赞记录
        like = super().create(validated_data)
        # 更新动态的点赞数
        activity.likes_count = activity.likes.count()
        activity.save()
        return like


class ActivityCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    activity = serializers.CharField(source='activity.id')
    parent = serializers.CharField(source='parent.id', allow_null=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = ActivityComment
        fields = ['id', 'user', 'activity', 'content', 'parent', 'replies', 'created_at']
    
    def get_replies(self, obj):
        if obj.replies.exists():
            return ActivityCommentSerializer(obj.replies.all(), many=True).data
        return []


class ActivityCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityComment
        fields = ['activity', 'content', 'parent']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        # 创建评论
        comment = super().create(validated_data)
        # 更新动态的评论数
        activity = comment.activity
        activity.comments_count = activity.comments.count()
        activity.save()
        return comment