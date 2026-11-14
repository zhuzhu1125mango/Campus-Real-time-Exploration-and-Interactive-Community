from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from learning.serializers import CourseSerializer
from content.serializers import ContentSerializer
from schools.serializers import SchoolSerializer
from forum.serializers import TopicListSerializer, PostSerializer
from users.serializers import UserPublicSerializer

from .services import SearchService


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def global_search(request):
    """全局聚合搜索：课程、内容、学校、论坛主题/帖子、用户。

    优先使用 Elasticsearch（ik 中文分词）；ES 不可用时降级为 MySQL LIKE 搜索。
    """
    query = request.query_params.get('q', '').strip()
    search_type = request.query_params.get('type', 'all')
    limit = min(int(request.query_params.get('limit', 10)), 50)

    if not query:
        return Response({'query': '', 'type': search_type, 'results': {}})

    service = SearchService()
    results = {}

    if search_type in ('all', 'course'):
        courses = service.search_courses(query, limit)
        results['courses'] = CourseSerializer(courses, many=True, context={'request': request}).data

    if search_type in ('all', 'content'):
        contents = service.search_contents(query, limit)
        results['contents'] = ContentSerializer(contents, many=True, context={'request': request}).data

    if search_type in ('all', 'school'):
        schools = service.search_schools(query, limit)
        results['schools'] = SchoolSerializer(schools, many=True, context={'request': request}).data

    if search_type in ('all', 'topic'):
        topics = service.search_topics(query, limit)
        results['topics'] = TopicListSerializer(topics, many=True, context={'request': request}).data

    if search_type in ('all', 'post'):
        posts = service.search_posts(query, limit)
        results['posts'] = PostSerializer(posts, many=True, context={'request': request}).data

    if search_type in ('all', 'user'):
        include_private = request.user.is_authenticated and request.user.is_staff
        users = service.search_users(query, limit, include_private=include_private, current_user=request.user)
        results['users'] = UserPublicSerializer(users, many=True, context={'request': request}).data

    return Response({'query': query, 'type': search_type, 'results': results})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_suggestions(request):
    """搜索建议：返回各类型前 5 条标题/名称。

    同样优先走 ES，失败时降级到数据库 LIKE。
    """
    query = request.query_params.get('q', '').strip()
    if not query:
        return Response({'query': '', 'suggestions': []})

    service = SearchService()
    suggestions = service.get_suggestions(query, limit=5)

    return Response({'query': query, 'suggestions': suggestions})
