from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action, api_view, parser_classes, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count, F
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
import csv
import io
from .models import (
    School, Major, SchoolMajor,
    SchoolRating, MajorRating, AdmissionScore, Event, EventRegistration
)
from .serializers import (
    SchoolSerializer, MajorSerializer,
    SchoolMajorSerializer, SchoolRatingSerializer,
    MajorRatingSerializer, AdmissionScoreSerializer, EventSerializer, EventRegistrationSerializer
)
from forum.models import Post as ForumPost
from forum.serializers import PostSerializer as ForumPostSerializer
from users.throttles import SearchThrottle, WriteThrottle

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
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'english_name', 'abbreviation', 'code']
    ordering_fields = ['name', 'founded_year', 'national_rank', 'student_count']
    ordering = ['national_rank', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'forums', 'majors', 'admission_scores', 'ratings', 'compare']:
            return [permissions.AllowAny()]

        # 尊重 @action(permission_classes=[...]) 的显式声明
        action = getattr(self, self.action, None)
        action_permission_classes = getattr(action, 'kwargs', {}).get('permission_classes')
        if action_permission_classes:
            return [permission() for permission in action_permission_classes]

        return [permissions.IsAdminUser()]

    def get_throttles(self):
        if self.action == 'list':
            return [SearchThrottle()]
        if self.action in ['rate', 'favorite', 'unfavorite', 'compare']:
            return [WriteThrottle()]
        return super().get_throttles()

    def perform_create(self, serializer):
        """创建学校时自动为其创建论坛板块"""
        school = serializer.save()
        # 延迟导入避免循环引用
        from forum.models import Board, Category
        category, _ = Category.objects.get_or_create(
            name='院校专区',
            defaults={
                'description': '各高校的讨论板块',
                'icon': 'el-icon-school',
                'order': 100
            }
        )
        Board.objects.get_or_create(
            school=school,
            defaults={
                'name': f'{school.name}论坛',
                'description': f'欢迎来到{school.name}论坛，这里是校友交流、分享资讯的地方。',
                'category': category,
                'icon': 'el-icon-school',
                'order': 0
            }
        )
        return school

    def get_queryset(self):
        # 预取关联数据，避免 N+1 查询
        queryset = School.objects.prefetch_related('majors__major', 'admission_scores', 'board')

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

    def list(self, request, *args, **kwargs):
        """缓存序列化后的结果，避免缓存 QuerySet 对象"""
        cache_key = f'schools_list_{request.query_params.urlencode()}'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(
            page if page is not None else queryset,
            many=True,
            context={'request': request}
        )
        data = serializer.data

        if page is not None:
            response = self.get_paginated_response(data)
            result = response.data
        else:
            response = Response(data)
            result = data

        # 缓存序列化结果，有效期5分钟
        cache.set(cache_key, result, 300)
        return response
    
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
                    # 确保学校论坛板块存在
                    from forum.models import Board, Category
                    category, _ = Category.objects.get_or_create(
                        name='院校专区',
                        defaults={
                            'description': '各高校的讨论板块',
                            'icon': 'el-icon-school',
                            'order': 100
                        }
                    )
                    Board.objects.get_or_create(
                        school=school,
                        defaults={
                            'name': f'{school.name}论坛',
                            'description': f'欢迎来到{school.name}论坛，这里是校友交流、分享资讯的地方。',
                            'category': category,
                            'icon': 'el-icon-school',
                            'order': 0
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
        """获取学校对应的论坛板块（不存在时自动创建）"""
        school = self.get_object()

        # 延迟导入避免循环引用
        from forum.models import Board, Category
        from forum.serializers import BoardDetailSerializer

        category, _ = Category.objects.get_or_create(
            name='院校专区',
            defaults={
                'description': '各高校的讨论板块',
                'icon': 'el-icon-school',
                'order': 100
            }
        )

        board, created = Board.objects.get_or_create(
            school=school,
            defaults={
                'name': f'{school.name}论坛',
                'description': f'欢迎来到{school.name}论坛，这里是校友交流、分享资讯的地方。',
                'category': category,
                'icon': 'el-icon-school',
                'order': 0
            }
        )

        serializer = BoardDetailSerializer(board, context={'request': request})
        return Response(serializer.data)
    
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
        
        # 同步到通用收藏模型
        from django.contrib.contenttypes.models import ContentType
        from users.favorites import Favorite
        content_type = ContentType.objects.get_for_model(school)
        Favorite.objects.get_or_create(
            user=user,
            content_type=content_type,
            object_id=school.id,
            defaults={'category': 'school'}
        )
        
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
        
        # 同步删除通用收藏记录
        from django.contrib.contenttypes.models import ContentType
        from users.favorites import Favorite
        content_type = ContentType.objects.get_for_model(school)
        Favorite.objects.filter(
            user=user,
            content_type=content_type,
            object_id=school.id
        ).delete()
        
        return Response({"detail": "取消收藏成功"}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def compare(self, request):
        """院校对比功能"""
        school_ids = request.data.get('school_ids', [])
        comparison_fields = request.data.get('comparison_fields', [])
        
        if not school_ids or len(school_ids) < 2:
            return Response({"detail": "至少需要选择2所院校进行对比"}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(school_ids) > 4:
            return Response({"detail": "最多只能对比4所院校"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 构建缓存键
        cache_key = f'schools_compare_{"-".join(sorted(map(str, school_ids)))}'
        
        # 尝试从缓存获取
        cached_result = cache.get(cache_key)
        if cached_result:
            return Response(cached_result, status=status.HTTP_200_OK)
        
        # 获取学校信息
        schools = School.objects.filter(id__in=school_ids)
        if len(schools) != len(school_ids):
            return Response({"detail": "部分院校不存在"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 构建对比数据
        compare_data = []
        for school in schools:
            school_data = {
                'id': school.id,
                'name': school.name,
                'abbreviation': school.abbreviation,
                'province': school.province,
                'city': school.city,
                'school_type': dict(School.SCHOOL_TYPES).get(school.school_type, school.school_type),
                'school_level': dict(School.SCHOOL_LEVELS).get(school.school_level, school.school_level),
                'founded_year': school.founded_year,
                'national_rank': school.national_rank,
                'student_count': school.student_count,
                'faculty_count': school.faculty_count,
                'campus_area': school.campus_area,
                'website': school.website,
                'description': school.description,
                'majors': [],
                'admission_scores': [],
                'average_rating': 0
            }
            
            # 获取学校专业
            school_majors = SchoolMajor.objects.filter(school=school, is_active=True)[:10]  # 只取前10个专业
            for sm in school_majors:
                school_data['majors'].append({
                    'id': sm.major.id,
                    'name': sm.major.name,
                    'code': sm.major.code,
                    'degree_type': dict(Major.DEGREE_TYPES).get(sm.major.degree_type, sm.major.degree_type),
                    'subject_category': dict(Major.SUBJECT_CATEGORIES).get(sm.major.subject_category, sm.major.subject_category)
                })
            
            # 获取录取分数线
            scores = AdmissionScore.objects.filter(school=school).order_by('-year')[:5]  # 只取近5年数据
            for score in scores:
                school_data['admission_scores'].append({
                    'year': score.year,
                    'province': score.province,
                    'score_type': score.score_type,
                    'min_score': score.min_score,
                    'avg_score': score.avg_score,
                    'ranking': score.ranking
                })
            
            # 获取平均评分
            avg_rating = SchoolRating.objects.filter(school=school).aggregate(Avg('rating'))['rating__avg']
            school_data['average_rating'] = round(avg_rating, 1) if avg_rating else 0
            
            compare_data.append(school_data)
        
        # 定义对比字段
        fields = [
            {'key': 'name', 'label': '学校名称', 'type': 'text'},
            {'key': 'abbreviation', 'label': '简称', 'type': 'text'},
            {'key': 'province', 'label': '省份', 'type': 'text'},
            {'key': 'city', 'label': '城市', 'type': 'text'},
            {'key': 'school_type', 'label': '学校类型', 'type': 'text'},
            {'key': 'school_level', 'label': '办学层次', 'type': 'text'},
            {'key': 'founded_year', 'label': '建校时间', 'type': 'number'},
            {'key': 'national_rank', 'label': '全国排名', 'type': 'number'},
            {'key': 'student_count', 'label': '学生人数', 'type': 'number'},
            {'key': 'faculty_count', 'label': '教职工人数', 'type': 'number'},
            {'key': 'campus_area', 'label': '校园面积', 'type': 'number'},
            {'key': 'average_rating', 'label': '平均评分', 'type': 'number'}
        ]
        
        result = {
            'schools': compare_data,
            'fields': fields
        }
        
        # 缓存结果，有效期10分钟
        cache.set(cache_key, result, 600)
        
        return Response(result, status=status.HTTP_200_OK)

# 添加专业视图集
class MajorViewSet(viewsets.ModelViewSet):
    """专业视图集"""
    queryset = Major.objects.all()
    serializer_class = MajorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'degree_type', 'subject_category']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'schools', 'ratings']:
            return [permissions.AllowAny()]

        # 尊重 @action(permission_classes=[...]) 的显式声明
        action = getattr(self, self.action, None)
        action_permission_classes = getattr(action, 'kwargs', {}).get('permission_classes')
        if action_permission_classes:
            return [permission() for permission in action_permission_classes]

        return [permissions.IsAdminUser()]

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
@permission_classes([permissions.AllowAny])
def get_provinces(request):
    """获取所有省份列表"""
    # 使用缓存减少数据库查询
    cache_key = 'provinces_list'
    provinces = cache.get(cache_key)
    if not provinces:
        # 从数据库中获取所有不重复的省份
        provinces = School.objects.values_list('province', flat=True).distinct().order_by('province')
        provinces = list(provinces)
        # 缓存1小时
        cache.set(cache_key, provinces, 3600)
    return Response(provinces)

# 添加城市API视图
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_cities(request):
    """根据省份获取城市列表"""
    province = request.query_params.get('province', None)
    if province:
        # 使用缓存减少数据库查询
        cache_key = f'cities_list_{province}'
        cities = cache.get(cache_key)
        if not cities:
            # 获取指定省份的所有城市
            cities = School.objects.filter(province=province).values_list('city', flat=True).distinct().order_by('city')
            cities = list(cities)
            # 缓存1小时
            cache.set(cache_key, cities, 3600)
        return Response(cities)
    return Response([], status=status.HTTP_400_BAD_REQUEST)

# 添加学校类型API视图
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_school_types(request):
    """获取所有学校类型"""
    types_dict = {}
    for key, value in School.SCHOOL_TYPES:
        types_dict[key] = value
    return Response(types_dict)

# 添加学校层次API视图
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_school_levels(request):
    """获取所有学校层次"""
    levels_dict = {}
    for key, value in School.SCHOOL_LEVELS:
        levels_dict[key] = value
    return Response(levels_dict)

# 添加专业类型API视图
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_major_types(request):
    """获取所有专业学位类型"""
    types_dict = {}
    for key, value in Major.DEGREE_TYPES:
        types_dict[key] = value
    return Response(types_dict)

# 添加专业门类API视图
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
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

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def log_user_activity(request):
    """记录用户行为"""
    user = request.user
    activity_type = request.data.get('activity_type')
    target_type = request.data.get('target_type')
    target_id = request.data.get('target_id')
    metadata = request.data.get('metadata', {})
    
    if not all([activity_type, target_type, target_id]):
        return Response({"detail": "缺少必要参数"}, status=status.HTTP_400_BAD_REQUEST)
    
    # 验证activity_type和target_type是否合法
    valid_activity_types = ['browse', 'search', 'favorite', 'compare', 'rate']
    valid_target_types = ['school', 'major', 'post', 'topic']
    
    if activity_type not in valid_activity_types:
        return Response({"detail": "无效的活动类型"}, status=status.HTTP_400_BAD_REQUEST)
    
    if target_type not in valid_target_types:
        return Response({"detail": "无效的目标类型"}, status=status.HTTP_400_BAD_REQUEST)
    
    # 创建用户行为记录
    try:
        from users.models import UserActivity
        UserActivity.objects.create(
            user=user,
            activity_type=activity_type,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata
        )
        return Response({"detail": "行为记录成功"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"detail": f"记录失败: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from .recommendation import RecommendationService
from .stats import StatsService

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_recommendations(request):
    """获取个性化推荐"""
    user = request.user
    recommendation_type = request.query_params.get('type', 'schools')
    limit = int(request.query_params.get('limit', 10))
    
    try:
        if request.user.is_authenticated:
            # 初始化推荐服务
            recommendation_service = RecommendationService(user)
            
            if recommendation_type == 'schools':
                # 获取学校推荐
                result = recommendation_service.get_school_recommendations(limit)
                serializer = SchoolSerializer(result['schools'], many=True)
                return Response({
                    'recommendations': serializer.data,
                    'reasoning': result['reasoning']
                }, status=status.HTTP_200_OK)
            elif recommendation_type == 'majors':
                # 获取专业推荐
                result = recommendation_service.get_major_recommendations(limit)
                serializer = MajorSerializer(result['majors'], many=True)
                return Response({
                    'recommendations': serializer.data,
                    'reasoning': result['reasoning']
                }, status=status.HTTP_200_OK)
            elif recommendation_type == 'posts':
                # 获取帖子推荐
                result = recommendation_service.get_post_recommendations(limit)
                serializer = ForumPostSerializer(result['posts'], many=True, context={'request': request})
                return Response({
                    'recommendations': serializer.data,
                    'reasoning': result['reasoning']
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"detail": "无效的推荐类型"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # 未登录用户返回默认推荐
            if recommendation_type == 'schools':
                default_recommendations = School.objects.filter(
                    national_rank__isnull=False
                ).order_by('national_rank')[:limit]
                serializer = SchoolSerializer(default_recommendations, many=True)
                return Response({
                    'recommendations': serializer.data,
                    'reasoning': ['基于全国排名推荐']
                }, status=status.HTTP_200_OK)
            elif recommendation_type == 'majors':
                default_recommendations = Major.objects.annotate(
                    rating_count=Count('ratings')
                ).order_by('-rating_count')[:limit]
                serializer = MajorSerializer(default_recommendations, many=True)
                return Response({
                    'recommendations': serializer.data,
                    'reasoning': ['推荐热门专业']
                }, status=status.HTTP_200_OK)
            elif recommendation_type == 'posts':
                from django.db.models import Count as _Count
                default_recommendations = ForumPost.objects.annotate(
                    like_count=_Count('likes'),
                    comment_count=_Count('comments')
                ).order_by('-like_count', '-comment_count')[:limit]
                serializer = ForumPostSerializer(default_recommendations, many=True, context={'request': request})
                return Response({
                    'recommendations': serializer.data,
                    'reasoning': ['推荐热门帖子']
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"detail": "无效的推荐类型"},
                    status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        # 如果推荐失败，返回默认推荐
        if recommendation_type == 'schools':
            default_recommendations = School.objects.filter(
                national_rank__isnull=False
            ).order_by('national_rank')[:limit]
            serializer = SchoolSerializer(default_recommendations, many=True)
            return Response({
                'recommendations': serializer.data,
                'reasoning': ['基于全国排名推荐']
            }, status=status.HTTP_200_OK)
        elif recommendation_type == 'majors':
            default_recommendations = Major.objects.annotate(
                rating_count=Count('ratings')
            ).order_by('-rating_count')[:limit]
            serializer = MajorSerializer(default_recommendations, many=True)
            return Response({
                'recommendations': serializer.data,
                'reasoning': ['推荐热门专业']
            }, status=status.HTTP_200_OK)
        elif recommendation_type == 'posts':
            from django.db.models import Count as _Count
            default_recommendations = ForumPost.objects.annotate(
                like_count=_Count('likes'),
                comment_count=_Count('comments')
            ).order_by('-like_count', '-comment_count')[:limit]
            serializer = ForumPostSerializer(default_recommendations, many=True, context={'request': request})
            return Response({
                'recommendations': serializer.data,
                'reasoning': ['推荐热门帖子']
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "无效的推荐类型"},
                status=status.HTTP_400_BAD_REQUEST)


class EventViewSet(viewsets.ModelViewSet):
    """校园活动视图集"""
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]

        # 尊重 @action(permission_classes=[...]) 的显式声明
        action = getattr(self, self.action, None)
        action_permission_classes = getattr(action, 'kwargs', {}).get('permission_classes')
        if action_permission_classes:
            return [permission() for permission in action_permission_classes]

        return [permissions.IsAdminUser()]

    def get_throttles(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'register', 'cancel_registration']:
            return [WriteThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        queryset = super().get_queryset()

        # 筛选条件
        school_id = self.request.query_params.get('school_id')
        if school_id:
            queryset = queryset.filter(school_id=school_id)
        
        start_date = self.request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(start_time__gte=start_date)
        
        end_date = self.request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(end_time__lte=end_date)
        
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_serializer_context(self):
        """添加请求到序列化器上下文"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def register(self, request, pk=None):
        """报名活动（带事务与行锁，防止并发超报）"""
        event = self.get_object()
        user = request.user

        with transaction.atomic():
            # 锁定活动行，防止并发导致超报
            event = Event.objects.select_for_update().get(pk=event.pk)

            # 检查是否已经报名
            if EventRegistration.objects.filter(event=event, user=user).exists():
                return Response({"detail": "您已经报名过此活动"}, status=status.HTTP_400_BAD_REQUEST)

            # 检查活动状态
            if event.status in ['completed', 'cancelled']:
                return Response({"detail": "活动已结束或已取消"}, status=status.HTTP_400_BAD_REQUEST)

            # 检查报名截止时间
            if event.registration_deadline and timezone.now() > event.registration_deadline:
                return Response({"detail": "报名已截止"}, status=status.HTTP_400_BAD_REQUEST)

            # 检查活动容量
            if event.capacity and event.registrations.count() >= event.capacity:
                return Response({"detail": "活动报名人数已达上限"}, status=status.HTTP_400_BAD_REQUEST)

            # 创建报名记录
            registration = EventRegistration.objects.create(
                event=event,
                user=user,
                status='pending',
                metadata=request.data.get('metadata', {})
            )

        serializer = EventRegistrationSerializer(registration, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel_registration(self, request, pk=None):
        """取消报名"""
        event = self.get_object()
        user = request.user
        
        # 查找报名记录
        try:
            registration = EventRegistration.objects.get(event=event, user=user)
        except EventRegistration.DoesNotExist:
            return Response({"detail": "您未报名此活动"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查活动状态
        if event.status in ['completed', 'cancelled']:
            return Response({"detail": "活动已结束或已取消"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 取消报名
        registration.status = 'cancelled'
        registration.save()
        
        return Response({"detail": "报名已取消"}, status=status.HTTP_200_OK)

class EventRegistrationViewSet(viewsets.ModelViewSet):
    """活动报名视图集"""
    queryset = EventRegistration.objects.all()
    serializer_class = EventRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """只返回当前用户的报名记录"""
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """自动设置用户为当前用户"""
        serializer.save(user=self.request.user)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_school_stats(request):
    """获取学校统计数据"""
    try:
        stats_service = StatsService()
        stats = stats_service.get_school_stats()
        return Response(stats, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"detail": f"获取统计数据失败: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_forum_stats(request):
    """获取论坛统计数据"""
    try:
        stats_service = StatsService()
        stats = stats_service.get_forum_stats()
        return Response(stats, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"detail": f"获取统计数据失败: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_event_stats(request):
    """获取活动统计数据"""
    try:
        stats_service = StatsService()
        stats = stats_service.get_event_stats()
        return Response(stats, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"detail": f"获取统计数据失败: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_user_stats(request):
    """获取用户统计数据"""
    try:
        stats_service = StatsService()
        stats = stats_service.get_user_stats()
        return Response(stats, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"detail": f"获取统计数据失败: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_dashboard_stats(request):
    """获取仪表盘综合统计数据"""
    try:
        stats_service = StatsService()
        stats = stats_service.get_dashboard_stats()
        return Response(stats, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"detail": f"获取统计数据失败: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
