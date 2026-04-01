from rest_framework import serializers
from django.contrib.auth import get_user_model
from .messages import Message

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    用户序列化器
    用于序列化私信中的用户信息
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar']


class MessageSerializer(serializers.ModelSerializer):
    """
    私信序列化器
    """
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'content', 'is_read', 'created_at', 'updated_at']


class MessageCreateSerializer(serializers.ModelSerializer):
    """
    创建私信的序列化器
    """
    class Meta:
        model = Message
        fields = ['receiver', 'content']
    
    def validate_receiver(self, value):
        """
        验证接收者不是发送者自己
        """
        sender = self.context['request'].user
        if value == sender:
            raise serializers.ValidationError('不能向自己发送消息')
        return value
    
    def validate_content(self, value):
        """
        验证消息内容不为空且长度合理
        """
        if not value.strip():
            raise serializers.ValidationError('消息内容不能为空')
        if len(value) > 1000:
            raise serializers.ValidationError('消息内容过长，请限制在1000字符以内')
        return value
    
    def create(self, validated_data):
        """
        创建私信
        """
        sender = self.context['request'].user
        receiver = validated_data['receiver']
        content = validated_data['content']
        
        return Message.objects.create(
            sender=sender,
            receiver=receiver,
            content=content
        )


class ConversationSerializer(serializers.Serializer):
    """
    对话序列化器
    """
    user = UserSerializer()
    last_message = MessageSerializer()
    unread_count = serializers.IntegerField()


class ConversationDetailSerializer(serializers.Serializer):
    """
    对话详情序列化器
    """
    user = UserSerializer()
    messages = MessageSerializer(many=True)
    unread_count = serializers.IntegerField()
