from rest_framework import serializers
from django.contrib.auth import get_user_model
from .friendship import FriendRequest, Friend

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    用户序列化器
    用于序列化好友请求和好友关系中的用户信息
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar']


class FriendRequestSerializer(serializers.ModelSerializer):
    """
    好友请求序列化器
    """
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    
    class Meta:
        model = FriendRequest
        fields = ['id', 'sender', 'receiver', 'status', 'created_at', 'updated_at']


class FriendRequestCreateSerializer(serializers.ModelSerializer):
    """
    创建好友请求的序列化器
    """
    receiver = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    class Meta:
        model = FriendRequest
        fields = ['receiver']
    
    def validate_receiver(self, value):
        """
        验证接收者不是发送者自己
        """
        sender = self.context['request'].user
        if value == sender:
            raise serializers.ValidationError('不能向自己发送好友请求')
        return value
    
    def create(self, validated_data):
        """
        创建好友请求
        """
        sender = self.context['request'].user
        receiver = validated_data['receiver']
        
        # 检查是否已经存在好友请求
        existing_request = FriendRequest.objects.filter(
            sender=sender, 
            receiver=receiver
        ).first()
        
        if existing_request:
            raise serializers.ValidationError('已经向该用户发送过好友请求')
        
        # 检查是否已经是好友
        if Friend.is_friend(sender, receiver):
            raise serializers.ValidationError('你们已经是好友了')
        
        return FriendRequest.objects.create(
            sender=sender,
            receiver=receiver
        )


class FriendSerializer(serializers.ModelSerializer):
    """
    好友关系序列化器
    """
    user1 = UserSerializer(read_only=True)
    user2 = UserSerializer(read_only=True)
    
    class Meta:
        model = Friend
        fields = ['id', 'user1', 'user2', 'created_at']


class FriendListSerializer(serializers.Serializer):
    """
    好友列表序列化器
    """
    friends = UserSerializer(many=True)
    count = serializers.IntegerField()
