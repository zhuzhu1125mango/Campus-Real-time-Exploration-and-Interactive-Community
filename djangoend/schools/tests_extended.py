from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import School, Major, SchoolMajor, AdmissionScore
from rest_framework import status

User = get_user_model()

class SchoolListAPITest(TestCase):
    """测试学校列表API"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建测试用户
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        
        # 创建测试学校
        self.school1 = School.objects.create(
            name='测试学校1',
            abbreviation='测试1',
            province='北京市',
            city='北京市',
            school_type='comprehensive',
            school_level='985',
            founded_year=1900,
            national_rank=1
        )
        
        self.school2 = School.objects.create(
            name='测试学校2',
            abbreviation='测试2',
            province='上海市',
            city='上海市',
            school_type='science',
            school_level='211',
            founded_year=1950,
            national_rank=20
        )
        
        self.school3 = School.objects.create(
            name='北京大学',
            abbreviation='北大',
            province='北京市',
            city='北京市',
            school_type='comprehensive',
            school_level='985',
            founded_year=1898,
            national_rank=2
        )
    
    def test_get_school_list(self):
        """测试获取学校列表API"""
        response = self.client.get('/api/schools/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertGreaterEqual(len(response.data['results']), 2)
    
    def test_filter_schools_by_province(self):
        """测试按省份筛选学校"""
        response = self.client.get('/api/schools/?province=北京市')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for school in response.data['results']:
            self.assertEqual(school['province'], '北京市')
    
    def test_filter_schools_by_school_type(self):
        """测试按学校类型筛选学校"""
        response = self.client.get('/api/schools/?school_type=comprehensive')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for school in response.data['results']:
            self.assertEqual(school['school_type'], 'comprehensive')
    
    def test_search_schools(self):
        """测试搜索学校"""
        response = self.client.get('/api/schools/?search=北京')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for school in response.data['results']:
            self.assertIn('北京', school['name'])
    
    def test_sort_schools(self):
        """测试排序学校"""
        # 按排名排序
        response = self.client.get('/api/schools/?sort_by=ranking')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if len(response.data['results']) >= 2:
            self.assertLessEqual(
                response.data['results'][0]['national_rank'],
                response.data['results'][1]['national_rank']
            )

class LocationAPITest(TestCase):
    """测试省份和城市API"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = APIClient()
        
        # 创建测试学校
        School.objects.create(
            name='测试学校1',
            province='北京市',
            city='北京市'
        )
        
        School.objects.create(
            name='测试学校2',
            province='北京市',
            city='海淀区'
        )
        
        School.objects.create(
            name='测试学校3',
            province='上海市',
            city='上海市'
        )
    
    def test_get_provinces(self):
        """测试获取省份列表API"""
        response = self.client.get('/api/schools/provinces/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('北京市', response.data)
        self.assertIn('上海市', response.data)
    
    def test_get_cities(self):
        """测试获取城市列表API"""
        # 测试获取北京市的城市列表
        response = self.client.get('/api/schools/cities/?province=北京市')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('北京市', response.data)
        self.assertIn('海淀区', response.data)
        
        # 测试获取上海市的城市列表
        response = self.client.get('/api/schools/cities/?province=上海市')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('上海市', response.data)
        
        # 测试无省份参数
        response = self.client.get('/api/schools/cities/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class SchoolTypeAPITest(TestCase):
    """测试学校类型和层次API"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = APIClient()
    
    def test_get_school_types(self):
        """测试获取学校类型API"""
        response = self.client.get('/api/schools/types/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
    
    def test_get_school_levels(self):
        """测试获取学校层次API"""
        response = self.client.get('/api/schools/levels/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)

class MajorAPITest(TestCase):
    """测试专业API"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # 创建测试学校
        self.school = School.objects.create(
            name='测试学校',
            province='北京市',
            city='北京市'
        )
        
        # 创建测试专业
        self.major1 = Major.objects.create(
            name='计算机科学与技术',
            code='080901',
            degree_type='bachelor',
            subject_category='engineering'
        )
        
        self.major2 = Major.objects.create(
            name='经济学',
            code='020101',
            degree_type='bachelor',
            subject_category='economics'
        )
        
        # 创建学校专业关联
        SchoolMajor.objects.create(
            school=self.school,
            major=self.major1,
            is_active=True
        )
        
        SchoolMajor.objects.create(
            school=self.school,
            major=self.major2,
            is_active=True
        )
    
    def test_get_major_list(self):
        """测试获取专业列表API"""
        response = self.client.get('/api/schools/majors/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
    
    def test_get_schools_by_major(self):
        """测试获取开设特定专业的学校"""
        response = self.client.get(f'/api/schools/majors/{self.major1.id}/schools/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

class AdmissionScoreAPITest(TestCase):
    """测试录取分数线API"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # 创建测试学校
        self.school = School.objects.create(
            name='测试学校',
            province='北京市',
            city='北京市'
        )
        
        # 创建测试专业
        self.major = Major.objects.create(
            name='计算机科学与技术',
            code='080901'
        )
        
        # 创建录取分数线
        self.score1 = AdmissionScore.objects.create(
            school=self.school,
            major=self.major,
            year=2023,
            province='北京市',
            score_type='science',
            min_score=650,
            avg_score=660
        )
        
        self.score2 = AdmissionScore.objects.create(
            school=self.school,
            major=self.major,
            year=2022,
            province='北京市',
            score_type='science',
            min_score=640,
            avg_score=650
        )
    
    def test_get_admission_scores(self):
        """测试获取录取分数线API"""
        response = self.client.get('/api/schools/admission-scores/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
    
    def test_filter_admission_scores_by_school(self):
        """测试按学校筛选录取分数线"""
        response = self.client.get(f'/api/schools/admission-scores/?school_id={self.school.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for score in response.data['results']:
            self.assertEqual(score['school'], self.school.id)
    
    def test_filter_admission_scores_by_year(self):
        """测试按年份筛选录取分数线"""
        response = self.client.get('/api/schools/admission-scores/?year=2023')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for score in response.data['results']:
            self.assertEqual(score['year'], 2023)

class SchoolFavoriteAPITest(TestCase):
    """测试学校收藏功能"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # 创建测试学校
        self.school1 = School.objects.create(
            name='测试学校1',
            province='北京市',
            city='北京市'
        )
        
        self.school2 = School.objects.create(
            name='测试学校2',
            province='上海市',
            city='上海市'
        )
    
    def test_favorite_school(self):
        """测试收藏学校"""
        response = self.client.post(f'/api/schools/{self.school1.id}/favorite/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], '收藏成功')
    
    def test_unfavorite_school(self):
        """测试取消收藏学校"""
        # 先收藏学校
        self.client.post(f'/api/schools/{self.school1.id}/favorite/')
        
        # 取消收藏
        response = self.client.post(f'/api/schools/{self.school1.id}/unfavorite/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], '取消收藏成功')
    
    def test_get_favorite_schools(self):
        """测试获取用户收藏的学校"""
        # 收藏学校
        self.client.post(f'/api/schools/{self.school1.id}/favorite/')
        self.client.post(f'/api/schools/{self.school2.id}/favorite/')
        
        # 获取收藏的学校
        response = self.client.get('/api/schools/favorite-schools/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
