from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.contenttypes.models import ContentType

from .favorites import Favorite
from .favorites_serializers import FavoriteSerializer, FavoriteCreateSerializer


class FavoriteViewSet(viewsets.ModelViewSet):
    """收藏夹视图集"""
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # 只返回当前用户的收藏
        return Favorite.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'add_favorite':
            return FavoriteCreateSerializer
        return self.serializer_class
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def add_favorite(self, request):
        """添加收藏"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        favorite = serializer.save()
        
        return Response({
            'id': favorite.id,
            'message': '收藏成功'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['delete'])
    def remove_favorite(self, request):
        """移除收藏"""
        content_type_str = request.data.get('content_type')
        object_id = request.data.get('object_id')
        
        if not content_type_str or not object_id:
            return Response({
                'error': '缺少必要参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            app_label, model = content_type_str.split('.')
            content_type = ContentType.objects.get(app_label=app_label, model=model)
        except (ValueError, ContentType.DoesNotExist):
            return Response({
                'error': '无效的内容类型'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 查找并删除收藏
        favorite = Favorite.objects.filter(
            user=request.user,
            content_type=content_type,
            object_id=object_id
        ).first()
        
        if not favorite:
            return Response({
                'error': '未找到该收藏'
            }, status=status.HTTP_404_NOT_FOUND)
        
        favorite.delete()
        
        return Response({
            'message': '已取消收藏'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def check_favorite(self, request):
        """检查是否已收藏"""
        content_type_str = request.query_params.get('content_type')
        object_id = request.query_params.get('object_id')
        
        if not content_type_str or not object_id:
            return Response({
                'error': '缺少必要参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            app_label, model = content_type_str.split('.')
            content_type = ContentType.objects.get(app_label=app_label, model=model)
        except (ValueError, ContentType.DoesNotExist):
            return Response({
                'error': '无效的内容类型'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查是否已收藏
        is_favorited = Favorite.objects.filter(
            user=request.user,
            content_type=content_type,
            object_id=object_id
        ).exists()
        
        return Response({
            'is_favorited': is_favorited
        })
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """按分类获取收藏"""
        category = request.query_params.get('category', '')
        queryset = self.get_queryset()
        
        if category:
            queryset = queryset.filter(category=category)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)