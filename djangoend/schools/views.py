from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action, api_view, parser_classes, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg
import csv
import io
from .models import (
    Forum, Post, Comment, Tag, School, Major, SchoolMajor, 
    SchoolRating, MajorRating, AdmissionScore
)
from .serializers import (
    ForumSerializer, PostSerializer, CommentSerializer, 
    TagSerializer, SchoolSerializer, MajorSerializer,
    SchoolMajorSerializer, SchoolRatingSerializer,
    MajorRatingSerializer, AdmissionScoreSerializer
)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def test_connection(request):
    """测试API连接"""
    return Response({"message": "API连接成功", "status": "OK"}, status=status.HTTP_200_OK)

# 添加学校视图集
class SchoolViewSet(viewsets.ModelViewSet):
    """学校视图集"""
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'english_name', 'abbreviation', 'code']
    ordering_fields = ['name', 'founded_year', 'national_rank', 'student_count']
    ordering = ['national_rank', 'name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 筛选条件
        province = self.request.query_params.get('province')
        if province:
            queryset = queryset.filter(province=province)
        
        school_type = self.request.query_params.get('school_type')
        if school_type:
            queryset = queryset.filter(school_type=school_type)
        
        school_level = self.request.query_params.get('school_level')
        if school_level:
            queryset = queryset.filter(school_level=school_level)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(english_name__icontains=search) |
                Q(abbreviation__icontains=search)
            )
        
        sort_by = self.request.query_params.get('sort_by')
        if sort_by == 'ranking':
            queryset = queryset.order_by('national_rank', 'name')
        elif sort_by == 'name':
            queryset = queryset.order_by('name')
        elif sort_by == 'founded_year':
            queryset = queryset.order_by('-founded_year', 'name')
        
        return queryset
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAdminUser])
    @parser_classes([MultiPartParser, FormParser])
    def import_csv(self, request):
        """导入学校数据CSV文件"""
        if 'file' not in request.FILES:
            return Response({"error": "请上传CSV文件"}, status=status.HTTP_400_BAD_REQUEST)
        
        csv_file = request.FILES['file']
        if not csv_file.name.endswith('.csv'):
            return Response({"error": "请上传CSV格式的文件"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 解码CSV文件
        try:
            csv_data = csv_file.read().decode('utf-8')
            io_string = io.StringIO(csv_data)
            reader = csv.DictReader(io_string)
            
            success_count = 0
            error_count = 0
            errors = []
            
            for row in reader:
                try:
                    # 检查必填字段
                    if not row.get('name') or not row.get('province'):
                        error_count += 1
                        continue
                    
                    # 创建或更新学校记录
                    school, created = School.objects.update_or_create(
                        name=row.get('name'),
                        defaults={
                            'english_name': row.get('english_name', ''),
                            'code': row.get('code', ''),
                            'abbreviation': row.get('abbreviation', ''),
                            'school_type': row.get('school_type', 'comprehensive'),
                            'school_level': row.get('school_level', 'ordinary'),
                            'founded_year': int(row.get('founded_year', 0)) if row.get('founded_year') else None,
                            'province': row.get('province', ''),
                            'city': row.get('city', ''),
                            'address': row.get('address', ''),
                            'website': row.get('website', ''),
                            'national_rank': int(row.get('national_rank', 0)) if row.get('national_rank') else None,
                        }
                    )
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append(f"行 {reader.line_num}: {str(e)}")
            
            result = {
                "success_count": success_count,
                "error_count": error_count,
                "total": success_count + error_count,
                "errors": errors[:10]  # 仅返回前10个错误
            }
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": f"CSV处理错误: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def forums(self, request, pk=None):
        """获取学校的论坛"""
        school = self.get_object()
        try:
            forum = school.forum
            serializer = ForumSerializer(forum)
            return Response(serializer.data)
        except Forum.DoesNotExist:
            return Response({"detail": "该学校没有论坛"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def majors(self, request, pk=None):
        """获取学校的专业列表"""
        school = self.get_object()
        school_majors = SchoolMajor.objects.filter(school=school, is_active=True)
        
        # 查询参数
        search = request.query_params.get('search')
        degree_type = request.query_params.get('degree_type')
        subject_category = request.query_params.get('subject_category')
        
        if search:
            school_majors = school_majors.filter(
                Q(major__name__icontains=search) |
                Q(major__code__icontains=search)
            )
        
        if degree_type:
            school_majors = school_majors.filter(major__degree_type=degree_type)
        
        if subject_category:
            school_majors = school_majors.filter(major__subject_category=subject_category)
        
        serializer = SchoolMajorSerializer(school_majors, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def admission_scores(self, request, pk=None):
        """获取学校的录取分数线"""
        school = self.get_object()
        
        # 查询参数
        year = request.query_params.get('year')
        province = request.query_params.get('province')
        score_type = request.query_params.get('score_type')
        major_id = request.query_params.get('major_id')
        
        scores = AdmissionScore.objects.filter(school=school)
        
        if year:
            scores = scores.filter(year=year)
        
        if province:
            scores = scores.filter(province=province)
        
        if score_type:
            scores = scores.filter(score_type=score_type)
        
        if major_id:
            scores = scores.filter(major_id=major_id)
        
        serializer = AdmissionScoreSerializer(scores, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def ratings(self, request, pk=None):
        """获取学校的评分列表"""
        school = self.get_object()
        
        # 分页参数
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        ratings = SchoolRating.objects.filter(school=school).order_by('-created_at')
        count = ratings.count()
        ratings_page = ratings[start:end]
        
        # 计算平均评分
        avg_rating = ratings.aggregate(Avg('rating'))['rating__avg']
        
        serializer = SchoolRatingSerializer(ratings_page, many=True)
        
        return Response({
            'results': serializer.data,
            'count': count,
            'avg_rating': round(avg_rating, 1) if avg_rating else 0
        })
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def rate(self, request, pk=None):
        """评价学校"""
        school = self.get_object()
        user = request.user
        
        # 验证请求数据
        rating = request.data.get('rating')
        comment = request.data.get('comment', '')
        
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return Response({"detail": "评分必须是1-5之间的整数"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建或更新评价
        rating_obj, created = SchoolRating.objects.update_or_create(
            school=school,
            user=user,
            defaults={'rating': rating, 'comment': comment}
        )
        
        return Response({
            'id': rating_obj.id,
            'rating': rating_obj.rating,
            'comment': rating_obj.comment,
            'created': created
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        """收藏学校"""
        school = self.get_object()
        user = request.user
        
        # 检查是否支持favorite_schools字段
        if not hasattr(user, 'favorite_schools'):
            return Response({"detail": "用户模型不支持收藏功能"}, status=status.HTTP_400_BAD_REQUEST)
        
        if school in user.favorite_schools.all():
            return Response({"detail": "已经收藏过此学校"}, status=status.HTTP_400_BAD_REQUEST)
        
        user.favorite_schools.add(school)
        return Response({"detail": "收藏成功"}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unfavorite(self, request, pk=None):
        """取消收藏学校"""
        school = self.get_object()
        user = request.user
        
        # 检查是否支持favorite_schools字段
        if not hasattr(user, 'favorite_schools'):
            return Response({"detail": "用户模型不支持收藏功能"}, status=status.HTTP_400_BAD_REQUEST)
        
        if school not in user.favorite_schools.all():
            return Response({"detail": "未收藏此学校"}, status=status.HTTP_400_BAD_REQUEST)
        
        user.favorite_schools.remove(school)
        return Response({"detail": "取消收藏成功"}, status=status.HTTP_200_OK)

# 添加专业视图集
class MajorViewSet(viewsets.ModelViewSet):
    """专业视图集"""
    queryset = Major.objects.all()
    serializer_class = MajorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'degree_type', 'subject_category']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 筛选条件
        degree_type = self.request.query_params.get('degree_type')
        if degree_type:
            queryset = queryset.filter(degree_type=degree_type)
        
        subject_category = self.request.query_params.get('subject_category')
        if subject_category:
            queryset = queryset.filter(subject_category=subject_category)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def schools(self, request, pk=None):
        """获取开设此专业的学校列表"""
        major = self.get_object()
        school_majors = SchoolMajor.objects.filter(major=major, is_active=True)
        schools = [sm.school for sm in school_majors]
        
        serializer = SchoolSerializer(schools, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def ratings(self, request, pk=None):
        """获取专业的评价列表"""
        major = self.get_object()
        ratings = MajorRating.objects.filter(major=major).order_by('-created_at')
        
        # 分页
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        count = ratings.count()
        ratings_page = ratings[start:end]
        
        # 计算平均评分
        avg_rating = ratings.aggregate(Avg('rating'))['rating__avg']
        
        serializer = MajorRatingSerializer(ratings_page, many=True)
        
        return Response({
            'results': serializer.data,
            'count': count,
            'avg_rating': round(avg_rating, 1) if avg_rating else 0
        })
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def rate(self, request, pk=None):
        """评价专业"""
        major = self.get_object()
        user = request.user
        
        # 验证请求数据
        rating = request.data.get('rating')
        comment = request.data.get('comment', '')
        
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return Response({"detail": "评分必须是1-5之间的整数"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建或更新评价
        rating_obj, created = MajorRating.objects.update_or_create(
            major=major,
            user=user,
            defaults={'rating': rating, 'comment': comment}
        )
        
        return Response({
            'id': rating_obj.id,
            'rating': rating_obj.rating,
            'comment': rating_obj.comment,
            'created': created
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

# 添加录取分数线视图集
class AdmissionScoreViewSet(viewsets.ModelViewSet):
    """录取分数线视图集"""
    queryset = AdmissionScore.objects.all()
    serializer_class = AdmissionScoreSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticatedOrReadOnly()]
        return super().get_permissions()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 筛选条件
        school_id = self.request.query_params.get('school_id')
        if school_id:
            queryset = queryset.filter(school_id=school_id)
        
        major_id = self.request.query_params.get('major_id')
        if major_id:
            queryset = queryset.filter(major_id=major_id)
        
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=year)
        
        province = self.request.query_params.get('province')
        if province:
            queryset = queryset.filter(province=province)
        
        score_type = self.request.query_params.get('score_type')
        if score_type:
            queryset = queryset.filter(score_type=score_type)
        
        return queryset

# 添加省份API视图
@api_view(['GET'])
def get_provinces(request):
    """获取所有省份列表"""
    # 从数据库中获取所有不重复的省份
    provinces = School.objects.values_list('province', flat=True).distinct().order_by('province')
    return Response(list(provinces))

# 添加城市API视图
@api_view(['GET'])
def get_cities(request):
    """根据省份获取城市列表"""
    province = request.query_params.get('province', None)
    if province:
        # 获取指定省份的所有城市
        cities = School.objects.filter(province=province).values_list('city', flat=True).distinct().order_by('city')
        return Response(list(cities))
    return Response([], status=status.HTTP_400_BAD_REQUEST)

# 添加学校类型API视图
@api_view(['GET'])
def get_school_types(request):
    """获取所有学校类型"""
    types_dict = {}
    for key, value in School.SCHOOL_TYPES:
        types_dict[key] = value
    return Response(types_dict)

# 添加学校层次API视图
@api_view(['GET'])
def get_school_levels(request):
    """获取所有学校层次"""
    levels_dict = {}
    for key, value in School.SCHOOL_LEVELS:
        levels_dict[key] = value
    return Response(levels_dict)

# 添加专业类型API视图
@api_view(['GET'])
def get_major_types(request):
    """获取所有专业学位类型"""
    types_dict = {}
    for key, value in Major.DEGREE_TYPES:
        types_dict[key] = value
    return Response(types_dict)

# 添加专业门类API视图
@api_view(['GET'])
def get_subject_categories(request):
    """获取所有专业学科门类"""
    categories_dict = {}
    for key, value in Major.SUBJECT_CATEGORIES:
        categories_dict[key] = value
    return Response(categories_dict)

# 获取用户收藏的学校
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_favorite_schools(request):
    """获取用户收藏的学校列表"""
    user = request.user
    
    # 检查是否支持favorite_schools字段
    if not hasattr(user, 'favorite_schools'):
        return Response({"detail": "用户模型不支持收藏功能"}, status=status.HTTP_400_BAD_REQUEST)
    
    favorite_schools = user.favorite_schools.all()
    serializer = SchoolSerializer(favorite_schools, many=True)
    return Response(serializer.data)

class ForumViewSet(viewsets.ModelViewSet):
    queryset = Forum.objects.all()
    serializer_class = ForumSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        forum = self.get_object()
        posts = forum.posts.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        post = self.get_object()
        if request.user in post.likes.all():
            post.likes.remove(request.user)
        else:
            post.likes.add(request.user)
        return Response({'status': 'success'})
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        post = self.get_object()
        comments = post.comments.filter(parent=None)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        comment = self.get_object()
        if request.user in comment.likes.all():
            comment.likes.remove(request.user)
        else:
            comment.likes.add(request.user)
        return Response({'status': 'success'})
    
    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        comment = self.get_object()
        replies = comment.replies.all()
        serializer = CommentSerializer(replies, many=True)
        return Response(serializer.data)

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        tag = self.get_object()
        posts = tag.posts.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data) 