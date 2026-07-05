import threading
import time

from concurrent.futures import ThreadPoolExecutor, as_completed

from django.test import override_settings, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import VerificationCode

User = get_user_model()


# 测试期间关闭 DRF 限流，避免并发测试因限流出现非预期失败
DISABLE_THROTTLE_SETTINGS = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {},
}


class UserBaseAPITest(APITestCase):
    """用户API测试基类，提供常用辅助方法。"""

    def setUp(self):
        cache.clear()

    def create_user(self, username, password='TestPass123!', **kwargs):
        return User.objects.create_user(
            username=username,
            password=password,
            **kwargs
        )

    def get_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token), str(refresh)

    def authenticate(self, user):
        access, _ = self.get_tokens(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        return access

    def create_email_verification(self, email, purpose='register'):
        response = self.client.post('/api/users/email-code/', {
            'email': email,
            'purpose': purpose
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return VerificationCode.objects.filter(
            email=email, code_type='email', is_used=False
        ).latest('created_at')

    def create_phone_verification(self, phone, purpose='register'):
        response = self.client.post('/api/users/phone-code/', {
            'phone': phone,
            'purpose': purpose
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return VerificationCode.objects.filter(
            phone=phone, code_type='phone', is_used=False
        ).latest('created_at')


class UserRegistrationTests(UserBaseAPITest):
    """用户注册相关测试。"""

    def test_register_with_email_code(self):
        """使用邮箱验证码注册应成功并标记为已验证。"""
        email = 'test@example.com'
        verification = self.create_email_verification(email)

        response = self.client.post('/api/users/users/', {
            'username': 'newuser',
            'email': email,
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
            'code': verification.code
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='newuser')
        self.assertTrue(user.is_verified)
        self.assertEqual(user.email, email)

    def test_register_with_phone_code(self):
        """使用手机验证码注册应成功并标记为已验证。"""
        phone = '13800138000'
        verification = self.create_phone_verification(phone)

        response = self.client.post('/api/users/users/', {
            'username': 'phoneuser',
            'phone': phone,
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
            'code': verification.code
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='phoneuser')
        self.assertTrue(user.is_verified)
        self.assertEqual(user.phone, phone)

    def test_register_without_code(self):
        """不提供验证码也能注册，但不应标记为已验证。"""
        response = self.client.post('/api/users/users/', {
            'username': 'unverifieduser',
            'email': 'unverified@example.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!'
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='unverifieduser')
        self.assertFalse(user.is_verified)

    def test_register_with_invalid_code(self):
        """提供无效验证码应注册失败。"""
        response = self.client.post('/api/users/users/', {
            'username': 'badcodeuser',
            'email': 'badcode@example.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
            'code': '000000'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='badcodeuser').exists())

    def test_register_duplicate_username(self):
        """重复用户名应注册失败。"""
        self.create_user('existinguser')
        response = self.client.post('/api/users/users/', {
            'username': 'existinguser',
            'email': 'dup@example.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch(self):
        """两次密码不一致应注册失败。"""
        response = self.client.post('/api/users/users/', {
            'username': 'mismatchuser',
            'email': 'mismatch@example.com',
            'password': 'TestPass123!',
            'password_confirm': 'DifferentPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_email_and_phone(self):
        """邮箱和手机必须至少提供一个。"""
        response = self.client.post('/api/users/users/', {
            'username': 'nocontactuser',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTests(UserBaseAPITest):
    """用户登录相关测试。"""

    def test_password_login_success(self):
        """正确的用户名密码应返回JWT令牌和用户信息。"""
        user = self.create_user('loginuser')
        response = self.client.post('/api/users/users/login/', {
            'username': 'loginuser',
            'password': 'TestPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_password_login_invalid(self):
        """错误的密码应登录失败。"""
        self.create_user('loginuser')
        response = self.client.post('/api/users/users/login/', {
            'username': 'loginuser',
            'password': 'WrongPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_disabled_user(self):
        """禁用用户无法登录。"""
        user = self.create_user('disableduser')
        user.is_active = False
        user.save()

        response = self.client.post('/api/users/users/login/', {
            'username': 'disableduser',
            'password': 'TestPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_code_login_success(self):
        """邮箱验证码登录应成功。"""
        email = 'emaillogin@example.com'
        user = self.create_user('emailloginuser', email=email)
        verification = self.create_email_verification(email, purpose='login')

        response = self.client.post('/api/users/email-code-login/', {
            'email': email,
            'code': verification.code
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_me_endpoint_authenticated(self):
        """已登录用户可以获取自身信息。"""
        user = self.create_user('meuser')
        self.authenticate(user)
        response = self.client.get('/api/users/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'meuser')

    def test_me_endpoint_unauthenticated(self):
        """未登录用户访问me应失败。"""
        response = self.client.get('/api/users/users/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenTests(UserBaseAPITest):
    """JWT Token 相关测试。"""

    def test_token_refresh(self):
        """使用refresh token可以换取新的access token。"""
        user = self.create_user('refreshuser')
        _, refresh = self.get_tokens(user)

        response = self.client.post('/api/token/refresh/', {
            'refresh': refresh
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_token_verify(self):
        """有效的access token可以通过验证。"""
        user = self.create_user('verifyuser')
        access, _ = self.get_tokens(user)

        response = self.client.post('/api/token/verify/', {
            'token': access
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_refresh_invalid(self):
        """无效的refresh token应刷新失败。"""
        response = self.client.post('/api/token/refresh/', {
            'refresh': 'invalid-token'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class VerificationCodeTests(UserBaseAPITest):
    """验证码发送与验证测试。"""

    def test_send_email_code_for_register(self):
        """注册场景发送邮箱验证码应创建记录。"""
        email = 'codetest@example.com'
        response = self.client.post('/api/users/email-code/', {
            'email': email,
            'purpose': 'register'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(VerificationCode.objects.filter(email=email).exists())

    def test_send_email_code_register_existing_email(self):
        """注册时向已存在邮箱发送验证码应失败。"""
        email = 'existingcode@example.com'
        self.create_user('codeuser', email=email)
        response = self.client.post('/api/users/email-code/', {
            'email': email,
            'purpose': 'register'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_code_email(self):
        """验证正确的邮箱验证码应返回valid=true。"""
        email = 'verify@example.com'
        user = self.create_user('verifycodeuser', email=email)
        verification = self.create_email_verification(email, purpose='login')

        response = self.client.post('/api/users/verify-code/', {
            'code': verification.code,
            'email': email,
            'code_type': 'email'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])
        self.assertEqual(response.data['user']['id'], user.id)

    def test_verify_code_invalid(self):
        """验证错误的验证码应失败。"""
        response = self.client.post('/api/users/verify-code/', {
            'code': '000000',
            'email': 'none@example.com',
            'code_type': 'email'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DailyCheckInTests(UserBaseAPITest):
    """每日签到测试。"""

    def test_daily_checkin_success(self):
        """首次签到应成功并增加积分。"""
        user = self.create_user('checkinuser')
        self.authenticate(user)
        response = self.client.post('/api/users/users/daily_checkin/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('points', response.data)
        self.assertIn('total_points', response.data)

    def test_daily_checkin_duplicate(self):
        """同一天重复签到应失败。"""
        user = self.create_user('checkinuser2')
        self.authenticate(user)
        self.client.post('/api/users/users/daily_checkin/')
        response = self.client.post('/api/users/users/daily_checkin/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(REST_FRAMEWORK=DISABLE_THROTTLE_SETTINGS)
class ConcurrentDailyCheckInTests(TransactionTestCase):
    """并发签到测试，必须使用 TransactionTestCase 让子线程看到已提交数据。"""

    def setUp(self):
        cache.clear()

    def test_concurrent_checkin_once(self):
        """并发签到应只成功一次。"""
        user = User.objects.create_user(
            username='concurrentcheckin',
            password='TestPass123!'
        )
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        results = []
        errors = []

        def checkin():
            # 关闭从主线程继承的连接，让当前线程获取独立连接
            connection.close()
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
            response = client.post('/api/users/users/daily_checkin/')
            if response.status_code == status.HTTP_200_OK:
                results.append(response.data)
            else:
                errors.append(response.status_code)
            return response.status_code

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(checkin) for _ in range(5)]
            for future in as_completed(futures):
                future.result()

        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 4)


class UserSearchTests(UserBaseAPITest):
    """用户搜索与敏感信息过滤测试。"""

    def test_search_public_fields_only(self):
        """普通用户搜索只能看到公开字段，不能看到邮箱和手机号。"""
        user = self.create_user('searchtarget', email='target@example.com', phone='13800138001')
        searcher = self.create_user('searcher')
        self.authenticate(searcher)

        response = self.client.get('/api/users/users/search/', {'q': 'searchtarget'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        data = response.data[0] if isinstance(response.data, list) else response.data['results'][0]
        self.assertNotIn('email', data)
        self.assertNotIn('phone', data)

    def test_search_admin_can_search_email(self):
        """管理员可以通过邮箱搜索到用户。"""
        email = 'adminsearch@example.com'
        user = self.create_user('adminsearchtarget', email=email)
        admin = self.create_user('adminsearcher', is_staff=True)
        self.authenticate(admin)

        response = self.client.get('/api/users/users/search/', {'q': email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data['results']
        self.assertTrue(any(u['id'] == user.id for u in results))

    def test_search_requires_query(self):
        """没有搜索关键词应返回400。"""
        user = self.create_user('queryuser')
        self.authenticate(user)
        response = self.client.get('/api/users/users/search/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfilePrivacyTests(UserBaseAPITest):
    """用户资料隐私测试。"""

    def test_retrieve_self_shows_sensitive(self):
        """查看自己的资料应包含邮箱和手机号。"""
        user = self.create_user('selfuser', email='self@example.com', phone='13800138002')
        self.authenticate(user)
        response = self.client.get(f'/api/users/users/{user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('email', response.data)
        self.assertIn('phone', response.data)

    def test_retrieve_other_hides_sensitive(self):
        """查看他人资料不应包含邮箱和手机号。"""
        other = self.create_user('otheruser', email='other@example.com', phone='13800138003')
        viewer = self.create_user('viewer')
        self.authenticate(viewer)
        response = self.client.get(f'/api/users/users/{other.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('email', response.data)
        self.assertNotIn('phone', response.data)
