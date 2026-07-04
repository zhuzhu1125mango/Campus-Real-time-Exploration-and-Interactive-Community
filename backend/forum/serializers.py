from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Category, Board, Topic, Post, Attachment,
    Like, Tag, Report, Notification, Bookmark,
    Comment, CommentLike
)
from django.utils import timezone

User = get_user_model()


class UserBriefSerializer(serializers.ModelSerializer):
    """用户简要信息序列化器"""
    class Meta:
        model = User
        fields = ('id', 'username', 'avatar')


class CategorySerializer(serializers.ModelSerializer):
    """论坛分类序列化器"""
    board_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'icon', 'order', 'created_at', 'board_count')
    
    def get_board_count(self, obj):
        return obj.boards.count()


class BoardListSerializer(serializers.ModelSerializer):
    """论坛板块列表序列化器"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    topic_count = serializers.SerializerMethodField()
    post_count = serializers.SerializerMethodField()
    last_post_time = serializers.SerializerMethodField()
    last_post_topic = serializers.SerializerMethodField()
    last_post_author = serializers.SerializerMethodField()
    
    class Meta:
        model = Board
        fields = (
            'id', 'name', 'description', 'icon', 'category', 'category_name',
            'is_active', 'topic_count', 'post_count', 'last_post_time',
            'last_post_topic', 'last_post_author', 'created_at'
        )
    
    def get_topic_count(self, obj):
        return obj.topic_count

    def get_post_count(self, obj):
        return obj.post_count

    def get_last_post_time(self, obj):
        last_post = obj.last_post
        if last_post:
            return last_post.created_at
        return None

    def get_last_post_topic(self, obj):
        last_post = obj.last_post
        if last_post:
            return {'id': last_post.topic.id, 'title': last_post.topic.title}
        return None
    
    def get_last_post_author(self, obj):
        last_post = obj.last_post
        if last_post and last_post.author:
            return {'id': last_post.author.id, 'username': last_post.author.username}
        return None


class BoardDetailSerializer(serializers.ModelSerializer):
    """论坛板块详情序列化器"""
    category = CategorySerializer(read_only=True)
    moderators = UserBriefSerializer(many=True, read_only=True)
    
    class Meta:
        model = Board
        fields = (
            'id', 'name', 'description', 'icon', 'category', 'order',
            'is_active', 'moderators', 'created_at', 'updated_at'
        )


class BoardCreateUpdateSerializer(serializers.ModelSerializer):
    """论坛板块创建和更新序列化器"""
    class Meta:
        model = Board
        fields = (
            'name', 'description', 'icon', 'category', 'order',
            'is_active', 'moderators'
        )


class TagSerializer(serializers.ModelSerializer):
    """标签序列化器"""
    topic_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'description', 'topic_count')

    def get_topic_count(self, obj):
        return obj.topics.count()


class TopicListSerializer(serializers.ModelSerializer):
    """主题列表序列化器"""
    author = UserBriefSerializer(read_only=True)
    board_name = serializers.CharField(source='board.name', read_only=True)
    reply_count = serializers.SerializerMethodField()
    last_reply_time = serializers.SerializerMethodField()
    last_reply_user = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Topic
        fields = (
            'id', 'title', 'author', 'board', 'board_name', 'status',
            'views', 'is_closed', 'created_at', 'updated_at',
            'reply_count', 'last_reply_time', 'last_reply_user', 'tags'
        )
    
    def get_reply_count(self, obj):
        # 减去首贴
        count = obj.post_count
        return count - 1 if count > 0 else 0
    
    def get_last_reply_time(self, obj):
        last_post = obj.last_post
        if last_post and not last_post.is_first_post:
            return last_post.created_at
        return None
    
    def get_last_reply_user(self, obj):
        last_post = obj.last_post
        if last_post and not last_post.is_first_post and last_post.author:
            return {'id': last_post.author.id, 'username': last_post.author.username}
        return None


class TopicDetailSerializer(serializers.ModelSerializer):
    """主题详情序列化器"""
    author = UserBriefSerializer(read_only=True)
    board = BoardListSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_bookmarked = serializers.SerializerMethodField()
    
    class Meta:
        model = Topic
        fields = (
            'id', 'title', 'author', 'board', 'status',
            'views', 'is_closed', 'created_at', 'updated_at',
            'tags', 'is_bookmarked'
        )
    
    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Bookmark.objects.filter(user=request.user, topic=obj).exists()
        return False


class TopicCreateSerializer(serializers.ModelSerializer):
    """主题创建序列化器"""
    content = serializers.CharField(write_only=True, required=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False, write_only=True
    )

    class Meta:
        model = Topic
        fields = ('id', 'title', 'board', 'content', 'tags')
        read_only_fields = ('id',)
    
    def create(self, validated_data):
        content = validated_data.pop('content')
        tag_names = validated_data.pop('tags', [])
        
        # 创建主题
        validated_data['author'] = self.context['request'].user
        topic = Topic.objects.create(**validated_data)
        
        # 创建首贴
        Post.objects.create(
            topic=topic,
            author=topic.author,
            content=content,
            is_first_post=True
        )
        
        # 添加标签
        for tag_name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            topic.tags.add(tag)
        
        return topic


class AttachmentSerializer(serializers.ModelSerializer):
    """附件序列化器"""
    class Meta:
        model = Attachment
        fields = (
            'id', 'filename', 'file', 'file_size',
            'file_type', 'download_count', 'created_at'
        )
        read_only_fields = ('filename', 'file_size', 'file_type', 'download_count')
    
    def create(self, validated_data):
        file = validated_data.get('file')
        validated_data['filename'] = file.name
        validated_data['file_size'] = file.size
        validated_data['file_type'] = file.content_type
        return super().create(validated_data)


class PostSerializer(serializers.ModelSerializer):
    """帖子序列化器"""
    author = UserBriefSerializer(read_only=True)
    topic_title = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    reviewed_by_username = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['id', 'topic', 'topic_title', 'author', 'content', 'is_first_post', 
                  'is_edited', 'edited_by', 'edited_at', 'created_at', 'updated_at',
                  'like_count', 'is_liked', 'content_status', 'review_note', 
                  'reviewed_by', 'reviewed_by_username', 'reviewed_at']
        read_only_fields = ['is_first_post', 'is_edited', 'edited_by', 'edited_at',
                          'content_status', 'review_note', 'reviewed_by', 'reviewed_at']
    
    def get_topic_title(self, obj):
        return obj.topic.title if obj.topic else None
    
    def get_like_count(self, obj):
        return obj.likes.count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_reviewed_by_username(self, obj):
        return obj.reviewed_by.username if obj.reviewed_by else None

    def validate_content(self, value):
        """验证内容字段，允许HTML但进行基本清理"""
        from django.utils.html import strip_tags
        # 检查是否为空（去除HTML标签后）
        if not strip_tags(value).strip():
            raise serializers.ValidationError("内容不能为空")
        # 返回原始HTML内容
        return value


class PostCreateSerializer(serializers.ModelSerializer):
    """帖子创建序列化器"""
    class Meta:
        model = Post
        fields = ('topic', 'content')
    
    def create(self, validated_data):
        # 默认新帖子需要审核
        validated_data['author'] = self.context['request'].user
        validated_data['content_status'] = 'pending'
        return super().create(validated_data)


class PostUpdateSerializer(serializers.ModelSerializer):
    """帖子更新序列化器"""
    class Meta:
        model = Post
        fields = ('content',)
    
    def update(self, instance, validated_data):
        # 如果内容变更，标记为已编辑并设置为待审核状态
        if instance.content != validated_data.get('content'):
            instance.is_edited = True
            instance.edited_by = self.context['request'].user
            instance.edited_at = timezone.now()
            # 编辑后需要重新审核
            instance.content_status = 'pending'
            instance.review_note = None
            instance.reviewed_by = None
            instance.reviewed_at = None
        
        return super().update(instance, validated_data)


class PostAuditSerializer(serializers.ModelSerializer):
    """帖子审核序列化器"""
    class Meta:
        model = Post
        fields = ('content_status', 'review_note')
    
    def update(self, instance, validated_data):
        # 设置审核信息
        instance.content_status = validated_data.get('content_status', instance.content_status)
        instance.review_note = validated_data.get('review_note', instance.review_note)
        instance.reviewed_by = self.context['request'].user
        instance.reviewed_at = timezone.now()
        
        # 如果审核不通过，通知作者
        if instance.content_status == 'rejected' and instance.author != self.context['request'].user:
            Notification.objects.create(
                user=instance.author,
                sender=self.context['request'].user,
                notification_type='system',
                topic=instance.topic,
                post=instance,
                message=f"您的帖子 \"{instance.topic.title}\" 未通过审核，原因：{instance.review_note}"
            )
        
        instance.save()
        return instance


class LikeSerializer(serializers.ModelSerializer):
    """点赞序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Like
        fields = ('id', 'post', 'user', 'username', 'created_at')
        read_only_fields = ('user', 'created_at')
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ReportCreateSerializer(serializers.ModelSerializer):
    """举报创建序列化器"""
    class Meta:
        model = Report
        fields = ('post', 'report_type', 'description')
    
    def create(self, validated_data):
        validated_data['reporter'] = self.context['request'].user
        validated_data['status'] = 'pending'
        return super().create(validated_data)


class BookmarkSerializer(serializers.ModelSerializer):
    """书签序列化器"""
    topic_title = serializers.CharField(source='topic.title', read_only=True)
    
    class Meta:
        model = Bookmark
        fields = ('id', 'topic', 'topic_title', 'created_at')
        read_only_fields = ('created_at',)
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    """通知序列化器"""
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    
    class Meta:
        model = Notification
        fields = (
            'id', 'user', 'sender', 'sender_username', 'notification_type',
            'topic', 'post', 'message', 'is_read', 'created_at'
        )
        read_only_fields = (
            'user', 'sender', 'notification_type', 'topic',
            'post', 'message', 'created_at'
        )


class CommentSerializer(serializers.ModelSerializer):
    """评论序列化器"""
    author = UserBriefSerializer(read_only=True)
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ('id', 'post', 'author', 'content', 'parent', 'created_at', 
                  'updated_at', 'like_count', 'is_liked', 'replies')
        read_only_fields = ('author', 'created_at', 'updated_at')
    
    def get_like_count(self, obj):
        return obj.like_count
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_replies(self, obj):
        request = self.context.get('request')
        replies = obj.replies.all()
        return CommentSerializer(replies, many=True, context={'request': request}).data


class CommentCreateSerializer(serializers.ModelSerializer):
    """评论创建序列化器"""
    class Meta:
        model = Comment
        fields = ('post', 'content', 'parent')
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        comment = Comment.objects.create(**validated_data)
        
        # 创建评论通知（如果评论的不是自己的帖子）
        if comment.post.author != self.context['request'].user:
            Notification.objects.create(
                user=comment.post.author,
                sender=self.context['request'].user,
                notification_type='topic_reply',
                post=comment.post,
                message=f"{self.context['request'].user.username} 评论了您的帖子"
            )
        
        return comment