from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import ContentType, Category, Tag, Content, Comment, ContentRevision
from .serializers import (
    ContentTypeSerializer, CategorySerializer, TagSerializer, 
    ContentSerializer, ContentCreateSerializer, ContentUpdateSerializer,
    CommentSerializer, CommentCreateSerializer, ContentRevisionSerializer
)
from rest_framework.permissions import IsAuthenticated, IsAdminUser


class ContentTypeViewSet(viewsets.ModelViewSet):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
    permission_classes = [IsAdminUser]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminUser]


class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ContentCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return ContentUpdateSerializer
        return ContentSerializer
    
    def perform_create(self, serializer):
        # 保存内容并创建修订历史
        content = serializer.save(author=self.request.user)
        ContentRevision.objects.create(
            content=content,
            author=self.request.user,
            title=content.title,
            content_text=content.content,
            summary=content.summary
        )
    
    def perform_update(self, serializer):
        # 保存内容并创建修订历史
        content = serializer.save()
        ContentRevision.objects.create(
            content=content,
            author=self.request.user,
            title=content.title,
            content_text=content.content,
            summary=content.summary
        )
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        content = self.get_object()
        content.is_published = True
        content.save()
        return Response({'status': 'published'})
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        content = self.get_object()
        content.is_published = False
        content.save()
        return Response({'status': 'unpublished'})
    
    @action(detail=True, methods=['get'])
    def revisions(self, request, pk=None):
        content = self.get_object()
        revisions = content.revisions.all()
        serializer = ContentRevisionSerializer(revisions, many=True)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CommentCreateSerializer
        return CommentSerializer
    
    def perform_create(self, serializer):
        # 保存评论并更新内容的评论计数
        comment = serializer.save(user=self.request.user)
        content = comment.content
        content.comment_count = content.comments.count()
        content.save()
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        comment = self.get_object()
        comment.is_approved = True
        comment.save()
        return Response({'status': 'approved'})
    
    @action(detail=True, methods=['post'])
    def disapprove(self, request, pk=None):
        comment = self.get_object()
        comment.is_approved = False
        comment.save()
        return Response({'status': 'disapproved'})