from rest_framework import viewsets, generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
import os
from django.http import HttpResponse
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.db.models import Q, F
from django.db import transaction

from .serializers import (
    UserSerializer, UserPublicSerializer, UserRegisterSerializer, UserLoginSerializer, UserProfileSerializer,
    PointsRecordSerializer, EmailVerificationSerializer, PhoneVerificationSerializer,
    VerifyCodeSerializer, EmailCodeLoginSerializer, PhoneCodeLoginSerializer, ResetPasswordSerializer
)
from schools.models import School
from forum.models import Topic, Post
from forum.serializers import TopicListSerializer, PostSerializer
from users.permissions import IsOwnerOrAdmin
from users.throttles import LoginThrottle, CodeSendThrottle, SearchThrottle, WriteThrottle

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegisterSerializer
        if self.action in ['search', 'list']:
            return UserPublicSerializer
        if self.action == 'retrieve':
            # retrieve 方法中根据访问者身份动态选择序列化器
            return UserPublicSerializer
        return self.serializer_class

    def get_permissions(self):
        if self.action in ['create', 'login', 'me', 'send_email_code', 'send_phone_code',
                           'verify_code', 'email_code_login', 'phone_code_login', 'reset_password']:
            return [permissions.AllowAny()]
        elif self.action == 'retrieve':
            return [permissions.AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        elif self.action in ['points', 'points_records']:
            # 积分信息仅本人或管理员可见
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        return super().get_permissions()

    def get_throttles(self):
        if self.action in ['login', 'email_code_login', 'phone_code_login']:
            return [LoginThrottle()]
        elif self.action in ['send_email_code', 'send_phone_code']:
            return [CodeSendThrottle()]
        elif self.action == 'search':
            return [SearchThrottle()]
        elif self.action in ['create', 'reset_password', 'daily_checkin']:
            return [WriteThrottle()]
        return super().get_throttles()

    def _is_self_or_admin(self, user):
        request_user = self.request.user
        return request_user.is_authenticated and (request_user == user or request_user.is_staff)

    def get_object(self):
        pk = self.kwargs.get('pk')
        if pk == 'me':
            if self.request.user.is_authenticated:
                return self.request.user
            else:
                from rest_framework.exceptions import AuthenticationFailed
                raise AuthenticationFailed('用户未登录')
        return super().get_object()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_class = UserSerializer if self._is_self_or_admin(instance) else UserPublicSerializer
        serializer = serializer_class(instance, context={'request': request})
        return Response(serializer.data)
    
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
        """用户登出，将 refresh token 加入黑名单"""
        if request.user.is_authenticated:
            # 删除 DRF Token（兼容旧逻辑）
            Token.objects.filter(user=request.user).delete()

            # 将传入的 refresh token 加入 JWT 黑名单
            refresh_token = request.data.get('refresh')
            if refresh_token:
                from rest_framework_simplejwt.tokens import RefreshToken
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except Exception:
                    pass

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
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def search(self, request):
        """搜索用户
        普通用户仅可通过用户名搜索；管理员额外支持邮箱/手机号搜索。
        返回用户公开信息，不暴露邮箱、手机号等敏感字段。
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': '搜索关键词不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        # 普通用户只能按用户名搜索；管理员可按邮箱/手机号搜索
        if request.user.is_authenticated and request.user.is_staff:
            users = User.objects.filter(
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query)
            )
        else:
            users = User.objects.filter(username__icontains=query)

        # 排除当前用户
        if request.user.is_authenticated:
            users = users.exclude(id=request.user.id)

        # 分页
        page = self.paginate_queryset(users)
        serializer = UserPublicSerializer(
            page if page is not None else users,
            many=True,
            context={'request': request}
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def send_email_code(self, request):
        """发送邮箱验证码"""
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'message': '验证码已发送'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def send_phone_code(self, request):
        """发送手机验证码"""
        serializer = PhoneVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'message': '验证码已发送'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def verify_code(self, request):
        """验证验证码是否有效"""
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get('user')
        return Response({
            'valid': True,
            'user': UserSerializer(user).data if user else None
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def email_code_login(self, request):
        """邮箱验证码登录"""
        serializer = EmailCodeLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # 更新最后登录时间
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # 使用JWT生成令牌
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        user_serializer = UserSerializer(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def phone_code_login(self, request):
        """手机验证码登录"""
        serializer = PhoneCodeLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # 更新最后登录时间
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # 使用JWT生成令牌
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        user_serializer = UserSerializer(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        """通过验证码重置密码"""
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({'message': '密码重置成功'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def points(self, request, pk=None):
        """获取用户积分信息"""
        user = self.get_object()
        
        data = {
            'points': user.points,
            'level': user.level,
            'level_name': user.level_name,
            'level_progress': user.level_progress,
            'next_level_points': user.next_level_points
        }
        
        return Response(data)
    
    @action(detail=True, methods=['get'])
    def points_records(self, request, pk=None):
        """获取用户积分记录"""
        user = self.get_object()
        records = user.points_records.all().order_by('-created_at')
        
        # 分页
        page = self.paginate_queryset(records)
        if page is not None:
            serializer = PointsRecordSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PointsRecordSerializer(records, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def daily_checkin(self, request):
        """每日签到（带事务与行锁，防止并发重复签到）"""
        from .models import PointsRecord
        from datetime import datetime, time, timedelta

        user = request.user
        today = timezone.now().date()
        today_start = timezone.make_aware(datetime.combine(today, time.min))
        tomorrow_start = timezone.make_aware(datetime.combine(today + timedelta(days=1), time.min))

        def has_checkin_on(date):
            start = timezone.make_aware(datetime.combine(date, time.min))
            end = timezone.make_aware(datetime.combine(date + timedelta(days=1), time.min))
            return PointsRecord.objects.filter(
                user=user,
                action='daily_checkin',
                created_at__gte=start,
                created_at__lt=end
            ).exists()

        with transaction.atomic():
            # 锁定用户行并重新加载，防止并发修改积分
            user = User.objects.select_for_update().get(pk=user.pk)

            # 锁定今天的签到记录（若存在），防止并发重复签到
            has_checked_in = PointsRecord.objects.filter(
                user=user,
                action='daily_checkin',
                created_at__gte=today_start,
                created_at__lt=tomorrow_start
            ).select_for_update().exists()

            if has_checked_in:
                return Response({'error': '今天已经签到过了'}, status=status.HTTP_400_BAD_REQUEST)

            # 添加签到积分（连续签到有额外奖励）
            points = 5
            yesterday = today - timedelta(days=1)
            yesterday_checkin = has_checkin_on(yesterday)

            consecutive_days = 0
            if yesterday_checkin:
                # 检查连续签到次数
                consecutive_days = 1
                check_date = yesterday
                while True:
                    check_date -= timedelta(days=1)
                    if has_checkin_on(check_date):
                        consecutive_days += 1
                    else:
                        break

                # 连续签到奖励
                if consecutive_days >= 7:
                    points += 10
                elif consecutive_days >= 3:
                    points += 5

            # 创建积分记录；post_save signal 会同步更新用户积分与等级
            PointsRecord.objects.create(
                user=user,
                action='daily_checkin',
                points=points,
                description=f'每日签到{"(连续签到{}天)".format(consecutive_days + 1) if yesterday_checkin else ""}'
            )
            # 重新加载以获取 signal 更新后的积分
            user.refresh_from_db()

        return Response({
            'message': '签到成功',
            'points': points,
            'total_points': user.points
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def follow(self, request, pk=None):
        """关注指定用户"""
        target = self.get_object()
        if target == request.user:
            return Response({'error': '不能关注自己'}, status=status.HTTP_400_BAD_REQUEST)
        request.user.following.add(target)
        return Response({'status': 'followed'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unfollow(self, request, pk=None):
        """取消关注指定用户"""
        target = self.get_object()
        request.user.following.remove(target)
        return Response({'status': 'unfollowed'})

# 添加调试视图，检查用户头像（仅在 DEBUG 模式下可用）
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def debug_avatar(request):
    """调试视图：检查用户头像状态"""
    if not settings.DEBUG:
        return Response({'error': '调试接口仅在 DEBUG 模式下可用'}, status=status.HTTP_404_NOT_FOUND)

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
    """测试静态文件服务（仅在 DEBUG 模式下可用）"""
    if not settings.DEBUG:
        return Response({'error': '调试接口仅在 DEBUG 模式下可用'}, status=status.HTTP_404_NOT_FOUND)

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
    """列出媒体文件夹中的所有头像文件（仅在 DEBUG 模式下可用）"""
    if not settings.DEBUG:
        return Response({'error': '调试接口仅在 DEBUG 模式下可用'}, status=status.HTTP_404_NOT_FOUND)

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

def test_html_media(request):
    """提供HTML测试页面（仅在 DEBUG 模式下可用）"""
    if not settings.DEBUG:
        return Response({'error': '调试接口仅在 DEBUG 模式下可用'}, status=status.HTTP_404_NOT_FOUND)

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


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def points_leaderboard(request):
    """获取积分排行榜"""
    top_users = User.objects.filter(is_active=True).order_by('-points')[:20]
    
    leaderboard = []
    for index, user in enumerate(top_users, start=1):
        leaderboard.append({
            'rank': index,
            'user_id': user.id,
            'username': user.username,
            'avatar': user.avatar.url if user.avatar else None,
            'points': user.points,
            'level': user.level,
            'level_name': user.level_name
        })
    
    return Response(leaderboard)


class UserProfileViewSet(viewsets.ModelViewSet):
    """用户资料视图集"""
    from .models import UserProfile
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action == 'retrieve':
            return [permissions.AllowAny()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=user)

    def get_object(self):
        pk = self.kwargs.get('pk')
        if pk == 'me':
            # 获取当前用户的资料，如果不存在则创建
            profile, created = UserProfile.objects.get_or_create(user=self.request.user)
            return profile
        return super().get_object()