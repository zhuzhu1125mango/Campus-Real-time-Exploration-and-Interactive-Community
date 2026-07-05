from django.utils.text import slugify
from rest_framework import serializers
from .models import ContentType, Category, Tag, Content, Comment, ContentRevision
from users.serializers import UserSerializer


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at']


class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.CharField(source='parent.name', allow_null=True, required=False)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'description', 'order', 'is_active', 'created_at', 'updated_at']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']


class ContentSerializer(serializers.ModelSerializer):
    content_type = ContentTypeSerializer()
    category = CategorySerializer(allow_null=True)
    tags = TagSerializer(many=True, allow_null=True)
    author = UserSerializer()
    featured_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Content
        fields = [
            'id', 'title', 'slug', 'content_type', 'category', 'tags', 'author',
            'content', 'summary', 'featured_image', 'is_published', 'status', 'publish_date',
            'view_count', 'comment_count', 'like_count', 'created_at', 'updated_at'
        ]
    
    def get_featured_image(self, obj):
        if obj.featured_image:
            return obj.featured_image.url
        return None


class ContentCreateSerializer(serializers.ModelSerializer):
    content_type = serializers.PrimaryKeyRelatedField(queryset=ContentType.objects.all())
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), allow_null=True, required=False)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, allow_null=True, required=False)
    slug = serializers.SlugField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=Content.STATUS_CHOICES, default='draft', required=False)

    class Meta:
        model = Content
        fields = [
            'id', 'title', 'slug', 'content_type', 'category', 'tags', 'content',
            'summary', 'featured_image', 'is_published', 'status'
        ]

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        if not validated_data.get('slug'):
            base = slugify(validated_data['title']) or 'content'
            slug = base
            counter = 1
            while Content.objects.filter(slug=slug).exists():
                slug = f'{base}-{counter}'
                counter += 1
            validated_data['slug'] = slug
        return super().create(validated_data)


class ContentUpdateSerializer(serializers.ModelSerializer):
    content_type = serializers.PrimaryKeyRelatedField(queryset=ContentType.objects.all())
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), allow_null=True, required=False)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, allow_null=True, required=False)
    slug = serializers.SlugField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=Content.STATUS_CHOICES, required=False)

    class Meta:
        model = Content
        fields = [
            'title', 'slug', 'content_type', 'category', 'tags', 'content',
            'summary', 'featured_image', 'is_published', 'status'
        ]


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    content = serializers.CharField(source='content.title')
    parent = serializers.CharField(source='parent.id', allow_null=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'content', 'user', 'parent', 'content_text', 'is_approved', 'created_at', 'updated_at']


class CommentCreateSerializer(serializers.ModelSerializer):
    content = serializers.PrimaryKeyRelatedField(queryset=Content.objects.all())
    parent = serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all(), allow_null=True)
    
    class Meta:
        model = Comment
        fields = ['content', 'parent', 'content_text']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ContentRevisionSerializer(serializers.ModelSerializer):
    content_title = serializers.CharField(source='content.title')
    author = UserSerializer()
    
    class Meta:
        model = ContentRevision
        fields = ['id', 'content_title', 'author', 'title', 'content_text', 'summary', 'created_at']