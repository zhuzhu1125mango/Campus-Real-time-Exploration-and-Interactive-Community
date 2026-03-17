from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import School, Major, SchoolMajor, AdmissionScore
from rest_framework import status

User = get_user_model()

class SchoolComparisonAPITest(TestCase):
    """测试院校对比功能的API"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建测试用户
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # 创建测试学校
        self.school1 = School.objects.create(
            name='测试学校1',
            abbreviation='测试1',
            province='北京市',
            city='北京市',
            school_type='comprehensive',
            school_level='985',
            founded_year=1900,
            national_rank=1,
            student_count=30000,
            faculty_count=2000,
            campus_area=100.5
        )
        
        self.school2 = School.objects.create(
            name='测试学校2',
            abbreviation='测试2',
            province='上海市',
            city='上海市',
            school_type='science',
            school_level='211',
            founded_year=1950,
            national_rank=20,
            student_count=20000,
            faculty_count=1500,
            campus_area=80.5
        )
        
        # 创建测试专业
        self.major = Major.objects.create(
            name='计算机科学与技术',
            code='080901',
            degree_type='bachelor',
            subject_category='engineering'
        )
        
        # 创建学校专业关联
        SchoolMajor.objects.create(
            school=self.school1,
            major=self.major,
            is_active=True
        )
        
        SchoolMajor.objects.create(
            school=self.school2,
            major=self.major,
            is_active=True
        )
        
        # 创建录取分数线
        AdmissionScore.objects.create(
            school=self.school1,
            year=2023,
            province='北京市',
            score_type='science',
            min_score=650,
            avg_score=660
        )
        
        AdmissionScore.objects.create(
            school=self.school2,
            year=2023,
            province='上海市',
            score_type='science',
            min_score=620,
            avg_score=630
        )
    
    def test_compare_schools(self):
        """测试院校对比API"""
        # 测试对比2所学校
        response = self.client.post('/api/schools/compare/', {
            'school_ids': [self.school1.id, self.school2.id],
            'comparison_fields': ['name', 'province', 'national_rank']
        }, format='json')
        
        # 打印响应信息，以便调试
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        print(f"School 1 ID: {self.school1.id}")
        print(f"School 2 ID: {self.school2.id}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('schools', response.data)
        self.assertIn('fields', response.data)
        self.assertEqual(len(response.data['schools']), 2)
        
        # 测试对比学校数量不足
        response = self.client.post('/api/schools/compare/', {
            'school_ids': [self.school1.id],
            'comparison_fields': ['name']
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 测试对比学校数量过多
        # 创建第3和第4所学校
        school3 = School.objects.create(
            name='测试学校3',
            abbreviation='测试3',
            province='广东省',
            city='广州市',
            school_type='liberal_arts',
            school_level='key'
        )
        
        school4 = School.objects.create(
            name='测试学校4',
            abbreviation='测试4',
            province='江苏省',
            city='南京市',
            school_type='normal',
            school_level='ordinary'
        )
        
        school5 = School.objects.create(
            name='测试学校5',
            abbreviation='测试5',
            province='浙江省',
            city='杭州市',
            school_type='finance',
            school_level='key'
        )
        
        response = self.client.post('/api/schools/compare/', {
            'school_ids': [self.school1.id, self.school2.id, school3.id, school4.id, school5.id],
            'comparison_fields': ['name']
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class RecommendationAPITest(TestCase):
    """测试推荐系统的API"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建测试用户
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # 创建测试学校
        for i in range(5):
            School.objects.create(
                name=f'测试学校{i+1}',
                abbreviation=f'测试{i+1}',
                province='北京市' if i < 3 else '上海市',
                city='北京市' if i < 3 else '上海市',
                school_type='comprehensive' if i < 3 else 'science',
                school_level='985' if i < 2 else '211',
                national_rank=i+1
            )
    
    def test_get_recommendations(self):
        """测试获取推荐API"""
        response = self.client.get('/api/schools/recommendations/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('recommendations', response.data)
        self.assertIn('reasoning', response.data)
        self.assertGreaterEqual(len(response.data['recommendations']), 0)

class EventAPITest(TestCase):
    """测试校园活动API"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建测试用户
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # 创建测试学校
        self.school = School.objects.create(
            name='测试学校',
            abbreviation='测试',
            province='北京市',
            city='北京市',
            school_type='comprehensive',
            school_level='985'
        )
        
        # 创建测试活动
        from django.utils import timezone
        from datetime import timedelta
        
        self.event = School.objects.get(name='测试学校').events.create(
            title='测试活动',
            description='测试活动描述',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            location='测试地点',
            organizer='测试组织者',
            capacity=100
        )
    
    def test_get_events(self):
        """测试获取活动列表API"""
        response = self.client.get('/api/schools/events/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
    
    def test_register_event(self):
        """测试报名活动API"""
        response = self.client.post(f'/api/schools/events/{self.event.id}/register/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 测试重复报名
        response = self.client.post(f'/api/schools/events/{self.event.id}/register/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_cancel_registration(self):
        """测试取消报名API"""
        # 先报名
        self.client.post(f'/api/schools/events/{self.event.id}/register/', format='json')
        
        # 取消报名
        response = self.client.post(f'/api/schools/events/{self.event.id}/cancel_registration/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class StatsAPITest(TestCase):
    """测试数据统计API"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建测试客户端（不强制认证）
        self.client = APIClient()
        
        # 创建测试学校
        for i in range(3):
            School.objects.create(
                name=f'测试学校{i+1}',
                abbreviation=f'测试{i+1}',
                province='北京市' if i == 0 else '上海市' if i == 1 else '广东省',
                city='北京市' if i == 0 else '上海市' if i == 1 else '广州市',
                school_type='comprehensive' if i == 0 else 'science' if i == 1 else 'liberal_arts',
                school_level='985' if i == 0 else '211' if i == 1 else 'key',
                national_rank=i+1,
                student_count=10000 + i*5000,
                faculty_count=500 + i*200,
                campus_area=50 + i*20
            )
    
    def test_get_dashboard_stats_unauthenticated(self):
        """测试未登录用户获取仪表盘统计数据API"""
        response = self.client.get('/api/schools/stats/dashboard/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('school_stats', response.data)
        self.assertIn('forum_stats', response.data)
        self.assertIn('event_stats', response.data)
        self.assertIn('user_stats', response.data)
        self.assertIn('last_updated', response.data)
    
    def test_get_school_stats_unauthenticated(self):
        """测试未登录用户获取学校统计数据API"""
        response = self.client.get('/api/schools/stats/school/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_schools', response.data)
        self.assertIn('type_distribution', response.data)
        self.assertIn('level_distribution', response.data)
        self.assertIn('province_distribution', response.data)
    
    def test_get_forum_stats_unauthenticated(self):
        """测试未登录用户获取论坛统计数据API"""
        response = self.client.get('/api/schools/stats/forum/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_posts', response.data)
        self.assertIn('total_comments', response.data)
        self.assertIn('recent_posts', response.data)
        self.assertIn('recent_comments', response.data)
    
    def test_get_event_stats_unauthenticated(self):
        """测试未登录用户获取活动统计数据API"""
        response = self.client.get('/api/schools/stats/event/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_events', response.data)
        self.assertIn('status_distribution', response.data)
        self.assertIn('total_registrations', response.data)
        self.assertIn('recent_events', response.data)
    
    def test_get_user_stats_unauthenticated(self):
        """测试未登录用户获取用户统计数据API"""
        response = self.client.get('/api/schools/stats/user/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_users', response.data)
        self.assertIn('recent_users', response.data)
        self.assertIn('activity_stats', response.data)
