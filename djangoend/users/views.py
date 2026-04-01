from rest_framework import viewsets, generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
import os
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from datetime import datetime
from django.shortcuts import get_object_or_404

from .serializers import (
    UserSerializer, UserRegisterSerializer, UserLoginSerializer, UserProfileSerializer
)
from schools.models import School
from forum.models import Topic, Post
from forum.serializers import TopicListSerializer, PostSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegisterSerializer
        return self.serializer_class
    
    def get_permissions(self):
        if self.action in ['create', 'login', 'me']:
            return [permissions.AllowAny()]
        elif self.action == 'retrieve':
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def get_object(self):
        pk = self.kwargs.get('pk')
        if pk == 'me':
            if self.request.user.is_authenticated:
                return self.request.user
            else:
                from rest_framework.exceptions import AuthenticationFailed
                raise AuthenticationFailed('用户未登录')
        return super().get_object()
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # 更新最后登录时间
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # 使用JWT生成令牌
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        # 获取用户数据
        user_serializer = UserSerializer(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        # 删除Token
        if request.user.is_authenticated:
            Token.objects.filter(user=request.user).delete()
        
        return Response({"detail": "成功登出。"}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """获取当前用户信息"""
        if request.user.is_authenticated:
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        else:
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed('用户未登录')
    
    @action(detail=False, methods=['patch'])
    def update_me(self, request):
        """更新当前用户信息"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def topics(self, request, pk=None):
        """获取用户创建的主题列表"""
        user = self.get_object()
        topics = Topic.objects.filter(author=user).order_by('-created_at')
        
        # 分页
        page = self.paginate_queryset(topics)
        if page is not None:
            serializer = TopicListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = TopicListSerializer(topics, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        """获取用户创建的帖子列表"""
        user = self.get_object()
        
        # 只显示已审核通过的帖子，除非是当前用户查看自己的帖子
        if request.user.is_authenticated and request.user.id == user.id:
            posts = Post.objects.filter(author=user).order_by('-created_at')
        else:
            posts = Post.objects.filter(author=user, content_status='approved').order_by('-created_at')
        
        # 过滤首贴
        include_first = request.query_params.get('include_first', 'false').lower() == 'true'
        if not include_first:
            posts = posts.filter(is_first_post=False)
        
        # 分页
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def profile_stats(self, request, pk=None):
        """获取用户资料统计信息"""
        user = self.get_object()
        
        # 统计数据
        topic_count = Topic.objects.filter(author=user).count()
        
        # 只显示已审核通过的帖子，除非是当前用户查看自己的帖子
        if request.user.is_authenticated and request.user.id == user.id:
            post_count = Post.objects.filter(author=user).count()
            reply_count = Post.objects.filter(author=user, is_first_post=False).count()
        else:
            post_count = Post.objects.filter(author=user, content_status='approved').count()
            reply_count = Post.objects.filter(author=user, is_first_post=False, content_status='approved').count()
        
        # 获取最活跃的版块
        from django.db.models import Count
        from forum.models import Board
        
        active_boards = []
        if request.user.is_authenticated and request.user.id == user.id:
            boards = Board.objects.filter(topics__posts__author=user).annotate(
                post_count=Count('topics__posts')
            ).order_by('-post_count')[:3]
            
            active_boards = [{'id': board.id, 'name': board.name, 'post_count': board.post_count} for board in boards]
        
        data = {
            'topic_count': topic_count,
            'post_count': post_count,
            'reply_count': reply_count,
            'active_boards': active_boards,
            'join_date': user.date_joined
        }
        
        return Response(data)

# 添加调试视图，检查用户头像
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def debug_avatar(request):
    """调试视图：检查用户头像状态"""
    users_with_avatar = User.objects.exclude(avatar='').exclude(avatar=None)
    users_data = []
    
    for user in users_with_avatar[:5]:  # 限制为前5个用户
        avatar_url = user.avatar.url if user.avatar else None
        absolute_url = request.build_absolute_uri(avatar_url) if avatar_url else None
        file_path = user.avatar.path if user.avatar else None
        
        users_data.append({
            'id': user.id,
            'username': user.username,
            'avatar_url': avatar_url,
            'absolute_url': absolute_url,
            'file_exists': file_path and os.path.exists(file_path),
            'file_path': file_path,
            'media_root': settings.MEDIA_ROOT,
            'media_url': settings.MEDIA_URL,
        })
    
    return JsonResponse({
        'users': users_data,
        'media_settings': {
            'MEDIA_ROOT': settings.MEDIA_ROOT,
            'MEDIA_URL': settings.MEDIA_URL,
            'DEBUG': settings.DEBUG,
        }
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def test_static_file(request):
    """测试静态文件服务"""
    return Response({
        'media_url': settings.MEDIA_URL,
        'static_url': settings.STATIC_URL,
        'test_image_url': '/media/avatars/avatar_1743088654593.jpg',
        'server_path': os.path.join(settings.MEDIA_ROOT, 'avatars', 'avatar_1743088654593.jpg'),
        'file_exists': os.path.exists(os.path.join(settings.MEDIA_ROOT, 'avatars', 'avatar_1743088654593.jpg')),
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def list_avatar_files(request):
    """列出媒体文件夹中的所有头像文件"""
    avatars_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
    if not os.path.exists(avatars_dir):
        return Response({
            'error': '头像目录不存在',
            'media_root': settings.MEDIA_ROOT,
            'avatars_dir': avatars_dir
        })
    
    files = os.listdir(avatars_dir)
    files_info = []
    
    for filename in files:
        file_path = os.path.join(avatars_dir, filename)
        url_path = f'/media/avatars/{filename}'
        absolute_url = request.build_absolute_uri(url_path)
        
        file_info = {
            'name': filename,
            'path': file_path,
            'url': url_path,
            'absolute_url': absolute_url,
            'size': os.path.getsize(file_path) if os.path.exists(file_path) else None,
            'exists': os.path.exists(file_path),
        }
        files_info.append(file_info)
    
    return Response({
        'media_root': settings.MEDIA_ROOT,
        'avatars_dir': avatars_dir,
        'files_count': len(files),
        'files': files_info
    })

@csrf_exempt
def test_html_media(request):
    """提供HTML测试页面"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>媒体文件测试</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                color: #333;
            }
            .image-container {
                margin-bottom: 30px;
            }
            img {
                max-width: 200px;
                border: 1px solid #ddd;
                margin-top: 10px;
            }
            .file-list {
                background: #f5f5f5;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <h1>媒体文件测试页面</h1>
        
        <div class="file-list">
            <h2>服务器信息</h2>
            <p>MEDIA_ROOT: {media_root}</p>
            <p>MEDIA_URL: {media_url}</p>
            <p>DEBUG: {debug}</p>
        </div>
        
        <div class="image-container">
            <h2>测试头像图片显示</h2>
            <div>
                <p>相对URL: /media/avatars/avatar_1743088654593.jpg</p>
                <img src="/media/avatars/avatar_1743088654593.jpg" alt="相对URL">
            </div>
            
            <div>
                <p>绝对URL: {absolute_url}/media/avatars/avatar_1743088654593.jpg</p>
                <img src="{absolute_url}/media/avatars/avatar_1743088654593.jpg" alt="绝对URL">
            </div>
            
            <div>
                <p>时间戳URL: {absolute_url}/media/avatars/avatar_1743088654593.jpg?_{timestamp}</p>
                <img src="{absolute_url}/media/avatars/avatar_1743088654593.jpg?_{timestamp}" alt="时间戳URL">
            </div>
        </div>

        <script>
            // 添加刷新按钮
            const refreshBtn = document.createElement('button');
            refreshBtn.textContent = '刷新测试';
            refreshBtn.style.padding = '10px 20px';
            refreshBtn.style.cursor = 'pointer';
            refreshBtn.style.marginBottom = '20px';
            refreshBtn.onclick = () => window.location.reload();
            document.body.insertBefore(refreshBtn, document.body.firstChild);
        </script>
    </body>
    </html>
    """.format(
        media_root=settings.MEDIA_ROOT,
        media_url=settings.MEDIA_URL,
        debug=settings.DEBUG,
        absolute_url=request.build_absolute_uri('/').rstrip('/'),
        timestamp=int(datetime.now().timestamp() * 1000)
    )
    
    return HttpResponse(html_content, content_type='text/html')


class UserProfileViewSet(viewsets.ModelViewSet):
    """用户资料视图集"""
    from .models import UserProfile
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action == 'retrieve':
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def get_object(self):
        pk = self.kwargs.get('pk')
        if pk == 'me':
            # 获取当前用户的资料，如果不存在则创建
            profile, created = UserProfile.objects.get_or_create(user=self.request.user)
            return profile
        return super().get_object()