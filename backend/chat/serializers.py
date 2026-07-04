from rest_framework import serializers
from .models import ChatMessage
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """用户简单序列化器"""
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar']
    
    def get_avatar(self, obj):
        if hasattr(obj, 'avatar') and obj.avatar:
            if hasattr(obj.avatar, 'url'):
                return obj.avatar.url
        return None


class ChatMessageSerializer(serializers.ModelSerializer):
    """聊天消息序列化器"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'content', 'user', 'created_at']
        read_only_fields = ['id', 'created_at', 'user'] 