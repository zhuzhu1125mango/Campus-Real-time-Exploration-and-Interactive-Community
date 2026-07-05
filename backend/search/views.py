from django.db.models import Q
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from learning.models import Course
from learning.serializers import CourseSerializer
from content.models import Content
from content.serializers import ContentSerializer
from schools.models import School
from schools.serializers import SchoolSerializer
from forum.models import Topic, Post
from forum.serializers import TopicListSerializer, PostSerializer


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def global_search(request):
    """全局聚合搜索：课程、内容、学校、论坛主题/帖子"""
    query = request.query_params.get('q', '').strip()
    search_type = request.query_params.get('type', 'all')
    limit = min(int(request.query_params.get('limit', 10)), 50)

    if not query:
        return Response({'query': '', 'results': {}})

    results = {}

    if search_type in ('all', 'course'):
        courses = Course.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(instructor__username__icontains=query),
            is_published=True
        ).distinct()[:limit]
        results['courses'] = CourseSerializer(courses, many=True, context={'request': request}).data

    if search_type in ('all', 'content'):
        contents = Content.objects.filter(
            Q(title__icontains=query) | Q(summary__icontains=query) | Q(content__icontains=query) | Q(author__username__icontains=query),
            status='published'
        ).distinct()[:limit]
        results['contents'] = ContentSerializer(contents, many=True, context={'request': request}).data

    if search_type in ('all', 'school'):
        schools = School.objects.filter(
            Q(name__icontains=query) | Q(english_name__icontains=query) | Q(abbreviation__icontains=query) | Q(code__icontains=query)
        ).distinct()[:limit]
        results['schools'] = SchoolSerializer(schools, many=True, context={'request': request}).data

    if search_type in ('all', 'topic'):
        topics = Topic.objects.filter(
            Q(title__icontains=query),
            ~Q(status='hidden')
        ).distinct()[:limit]
        results['topics'] = TopicListSerializer(topics, many=True, context={'request': request}).data

    if search_type in ('all', 'post'):
        posts = Post.objects.filter(
            Q(content__icontains=query) | Q(topic__title__icontains=query),
            content_status='approved'
        ).select_related('topic', 'author').distinct()[:limit]
        results['posts'] = PostSerializer(posts, many=True, context={'request': request}).data

    return Response({'query': query, 'type': search_type, 'results': results})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_suggestions(request):
    """搜索建议：返回各类型前 5 条标题/名称"""
    query = request.query_params.get('q', '').strip()
    if not query:
        return Response({'query': '', 'suggestions': []})

    suggestions = []

    courses = Course.objects.filter(title__icontains=query, is_published=True)[:5]
    for course in courses:
        suggestions.append({'type': 'course', 'id': course.id, 'title': course.title})

    contents = Content.objects.filter(title__icontains=query, status='published')[:5]
    for content in contents:
        suggestions.append({'type': 'content', 'id': content.id, 'title': content.title, 'slug': content.slug})

    schools = School.objects.filter(name__icontains=query)[:5]
    for school in schools:
        suggestions.append({'type': 'school', 'id': school.id, 'title': school.name})

    topics = Topic.objects.filter(title__icontains=query).exclude(status='hidden')[:5]
    for topic in topics:
        suggestions.append({'type': 'topic', 'id': topic.id, 'title': topic.title})

    return Response({'query': query, 'suggestions': suggestions})
