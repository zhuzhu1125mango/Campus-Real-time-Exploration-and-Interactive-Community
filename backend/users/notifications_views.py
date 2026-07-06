from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q

from .notifications import Notification
from .notifications_serializers import NotificationSerializer, NotificationCreateSerializer
from .notification_sender import send_notification


class NotificationViewSet(viewsets.ModelViewSet):
    """通知视图集"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        # 只返回当前用户的通知
        return Notification.objects.filter(recipient=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'send_notification':
            return NotificationCreateSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        notification = serializer.save(sender=self.request.user)
        # 发送实时通知
        send_notification(notification)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """获取未读通知"""
        queryset = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """将所有通知标记为已读"""
        Notification.mark_all_as_read(request.user)
        return Response({
            'message': '所有通知已标记为已读'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """将单个通知标记为已读"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({
            'message': '通知已标记为已读'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def count(self, request):
        """获取未读通知数量"""
        count = Notification.get_unread_count(request.user)
        return Response({
            'unread_count': count
        })
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """按类型获取通知"""
        notification_type = request.query_params.get('type')
        if not notification_type:
            return Response({
                'error': '缺少类型参数'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        queryset = self.get_queryset().filter(notification_type=notification_type)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def send_notification(self, request):
        """发送通知（仅管理员可调用，防止普通用户越权发送系统通知）"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = serializer.save()

        # 发送实时通知
        send_notification(notification)

        return Response({
            'id': notification.id,
            'message': '通知发送成功'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['delete'])
    def delete_all_read(self, request):
        """删除所有已读通知"""
        count = self.get_queryset().filter(is_read=True).delete()[0]
        return Response({
            'message': f'已删除{count}条已读通知'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def type_counts(self, request):
        """按类型获取通知数量"""
        from django.db.models import Count
        
        # 按类型分组统计通知数量
        type_counts = self.get_queryset().values('notification_type').annotate(count=Count('id'))
        
        # 转换为字典格式
        result = {}
        for item in type_counts:
            result[item['notification_type']] = item['count']
        
        return Response(result)