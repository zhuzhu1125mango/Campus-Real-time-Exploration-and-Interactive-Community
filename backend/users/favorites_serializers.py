from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from .favorites import Favorite

User = get_user_model()


class FavoriteSerializer(serializers.ModelSerializer):
    """收藏基本信息序列化器"""
    content_type = serializers.SerializerMethodField()
    content_type_name = serializers.ReadOnlyField()
    content_object_name = serializers.ReadOnlyField()
    content_object = serializers.SerializerMethodField()

    class Meta:
        model = Favorite
        fields = ('id', 'user', 'content_type', 'object_id', 'category',
                  'note', 'created_at', 'content_type_name', 'content_object_name', 'content_object')
        read_only_fields = ('id', 'user', 'created_at')

    def get_content_type(self, obj):
        return f"{obj.content_type.app_label}.{obj.content_type.model}"

    def get_content_object(self, obj):
        """返回被收藏对象的可序列化基本信息"""
        if obj.content_object is None:
            return None
        content = obj.content_object
        data = {}
        if hasattr(content, 'id'):
            data['id'] = content.id
        if hasattr(content, 'name'):
            data['name'] = content.name
        if hasattr(content, 'province'):
            data['province'] = content.province
        if hasattr(content, 'city'):
            data['city'] = content.city
        if hasattr(content, 'image'):
            try:
                data['image'] = content.image.url if content.image else None
            except Exception:
                data['image'] = None
        if hasattr(content, 'logo'):
            try:
                data['logo'] = content.logo.url if content.logo else None
            except Exception:
                data['logo'] = None
        if hasattr(content, 'school_level'):
            data['school_level'] = content.school_level
        if hasattr(content, 'school_type'):
            data['school_type'] = content.school_type
        if hasattr(content, 'national_rank'):
            data['national_rank'] = content.national_rank
        if hasattr(content, 'introduction'):
            data['introduction'] = content.introduction
        return data
    
    def create(self, validated_data):
        # 设置当前用户为收藏创建者
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class FavoriteCreateSerializer(serializers.Serializer):
    """创建收藏的序列化器"""
    content_type = serializers.CharField(required=True, help_text='内容类型，格式为：app_label.model_name')
    object_id = serializers.IntegerField(required=True, help_text='对象ID')
    category = serializers.CharField(required=False, allow_blank=True, help_text='分类')
    note = serializers.CharField(required=False, allow_blank=True, help_text='备注')
    
    def validate_content_type(self, value):
        try:
            app_label, model = value.split('.')
            content_type = ContentType.objects.get(app_label=app_label, model=model)
            return content_type
        except (ValueError, ContentType.DoesNotExist):
            raise serializers.ValidationError("无效的内容类型格式，应为'app_label.model_name'")
    
    def validate(self, attrs):
        # 检查是否已经收藏过
        user = self.context['request'].user
        content_type = attrs.get('content_type')
        object_id = attrs.get('object_id')
        
        if Favorite.objects.filter(user=user, content_type=content_type, object_id=object_id).exists():
            raise serializers.ValidationError("您已经收藏过此内容")
        
        # 检查对象是否存在
        try:
            model_class = content_type.model_class()
            model_class.objects.get(pk=object_id)
        except model_class.DoesNotExist:
            raise serializers.ValidationError("收藏的对象不存在")
        
        return attrs
    
    def create(self, validated_data):
        user = self.context['request'].user
        return Favorite.objects.create(user=user, **validated_data)