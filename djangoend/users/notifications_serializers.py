from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from .notifications import Notification

User = get_user_model()


class NotificationSerializer(serializers.ModelSerializer):
    """通知基本信息序列化器"""
    sender_username = serializers.SerializerMethodField()
    content_type_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = ('id', 'recipient', 'sender', 'sender_username', 'notification_type', 
                  'title', 'content', 'content_type', 'content_type_name', 'object_id', 
                  'url', 'is_read', 'created_at', 'updated_at')
        read_only_fields = ('id', 'recipient', 'created_at', 'updated_at')
    
    def get_sender_username(self, obj):
        """获取发送者用户名"""
        if obj.sender:
            return obj.sender.username
        return None
    
    def get_content_type_name(self, obj):
        """获取内容类型名称"""
        if obj.content_type:
            return obj.content_type.name
        return None


class NotificationCreateSerializer(serializers.ModelSerializer):
    """创建通知的序列化器"""
    content_type = serializers.CharField(required=False, allow_null=True, 
                                        help_text='内容类型，格式为：app_label.model_name')
    
    class Meta:
        model = Notification
        fields = ('recipient', 'notification_type', 'title', 'content', 
                  'content_type', 'object_id', 'url')
    
    def validate_content_type(self, value):
        if not value:
            return None
            
        try:
            app_label, model = value.split('.')
            content_type = ContentType.objects.get(app_label=app_label, model=model)
            return content_type
        except (ValueError, ContentType.DoesNotExist):
            raise serializers.ValidationError("无效的内容类型格式，应为'app_label.model_name'")
    
    def validate(self, attrs):
        # 验证content_type和object_id的一致性
        content_type = attrs.get('content_type')
        object_id = attrs.get('object_id')
        
        if (content_type and not object_id) or (not content_type and object_id):
            raise serializers.ValidationError("content_type和object_id必须同时提供或同时不提供")
        
        # 如果提供了content_type和object_id，验证对象是否存在
        if content_type and object_id:
            try:
                model_class = content_type.model_class()
                model_class.objects.get(pk=object_id)
            except model_class.DoesNotExist:
                raise serializers.ValidationError("关联的对象不存在")
        
        return attrs
    
    def create(self, validated_data):
        # 设置当前用户为通知发送者
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)