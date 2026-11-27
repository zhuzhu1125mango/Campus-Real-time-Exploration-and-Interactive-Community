from concurrent.futures import ThreadPoolExecutor, as_completed

from django.test import override_settings, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Course, Chapter, Lesson, Enrollment, Progress, Review, LearningResource,
    PaymentOrder, Certificate,
)

User = get_user_model()


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


class LearningBaseAPITest(APITestCase):
    """学习模块 API 测试基类。"""

    def setUp(self):
        cache.clear()

    def create_user(self, username, password='TestPass123!', **kwargs):
        if 'email' not in kwargs:
            kwargs['email'] = f'{username}@example.com'
        return User.objects.create_user(username=username, password=password, **kwargs)

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

    def create_course(self, instructor, is_published=True, **kwargs):
        defaults = {
            'title': 'Test Course',
            'slug': f'test-course-{Course.objects.count()}',
            'description': 'Test description',
            'is_published': is_published,
        }
        defaults.update(kwargs)
        return Course.objects.create(instructor=instructor, **defaults)

    def create_chapter(self, course, **kwargs):
        defaults = {'title': 'Test Chapter', 'order': 0}
        defaults.update(kwargs)
        return Chapter.objects.create(course=course, **defaults)

    def create_lesson(self, chapter, **kwargs):
        defaults = {'title': 'Test Lesson', 'order': 0}
        defaults.update(kwargs)
        return Lesson.objects.create(chapter=chapter, **defaults)


class EnrollmentTests(LearningBaseAPITest):
    """课程报名测试。"""

    def test_enroll_course_success(self):
        """报名课程应成功并更新报名人数。"""
        user = self.create_user('enrolluser')
        instructor = self.create_user('instructor')
        course = self.create_course(instructor)
        self.authenticate(user)

        response = self.client.post('/api/learning/enrollments/', {'course': course.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Enrollment.objects.filter(user=user, course=course).exists())
        course.refresh_from_db()
        self.assertEqual(course.enroll_count, 1)

    def test_enroll_duplicate_returns_existing(self):
        """重复报名应返回已有记录。"""
        user = self.create_user('enrolluser2')
        instructor = self.create_user('instructor2')
        course = self.create_course(instructor)
        self.authenticate(user)

        self.client.post('/api/learning/enrollments/', {'course': course.id})
        response = self.client.post('/api/learning/enrollments/', {'course': course.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Enrollment.objects.filter(user=user, course=course).count(), 1)


@override_settings(REST_FRAMEWORK=DISABLE_THROTTLE_SETTINGS)
class ConcurrentEnrollmentTests(TransactionTestCase):
    """并发报名测试。"""

    def setUp(self):
        cache.clear()

    def test_concurrent_enroll_once(self):
        """并发报名应只创建一条报名记录。"""
        user = User.objects.create_user(
            username='concurrentenroll', password='TestPass123!',
            email='concurrentenroll@example.com'
        )
        instructor = User.objects.create_user(
            username='enrollinstructor', password='TestPass123!',
            email='enrollinstructor@example.com'
        )
        course = Course.objects.create(
            title='Concurrent Course',
            slug='concurrent-course',
            description='desc',
            instructor=instructor,
            is_published=True
        )
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        results = []

        def enroll():
            connection.close()
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
            response = client.post('/api/learning/enrollments/', {'course': course.id})
            results.append(response.status_code)
            return response.status_code

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(enroll) for _ in range(5)]
            for future in as_completed(futures):
                future.result()

        self.assertEqual(Enrollment.objects.filter(user=user, course=course).count(), 1)
        self.assertEqual(results.count(status.HTTP_201_CREATED), 1)
        course.refresh_from_db()
        self.assertEqual(course.enroll_count, 1)


class ProgressTests(LearningBaseAPITest):
    """学习进度测试。"""

    def test_record_progress_updates_enrollment(self):
        """记录课时进度应更新报名总体进度。"""
        user = self.create_user('progressuser')
        instructor = self.create_user('progressinstructor')
        course = self.create_course(instructor)
        chapter = self.create_chapter(course)
        lesson1 = self.create_lesson(chapter, title='Lesson 1')
        lesson2 = self.create_lesson(chapter, title='Lesson 2')
        enrollment = Enrollment.objects.create(user=user, course=course)
        Progress.objects.create(enrollment=enrollment, lesson=lesson1)
        Progress.objects.create(enrollment=enrollment, lesson=lesson2)
        self.authenticate(user)

        response = self.client.post('/api/learning/progresses/record/', {
            'enrollment': enrollment.id,
            'lesson': lesson1.id,
            'is_completed': True
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.progress, 50.0)


@override_settings(REST_FRAMEWORK=DISABLE_THROTTLE_SETTINGS)
class ConcurrentProgressTests(TransactionTestCase):
    """并发进度更新测试。"""

    def setUp(self):
        cache.clear()

    def test_concurrent_progress_updates(self):
        """并发完成不同课时应正确计算总体进度。"""
        user = User.objects.create_user(
            username='concurrentprogress', password='TestPass123!',
            email='concurrentprogress@example.com'
        )
        instructor = User.objects.create_user(
            username='progressinstructor', password='TestPass123!',
            email='progressinstructor@example.com'
        )
        course = Course.objects.create(
            title='Progress Course',
            slug='progress-course',
            description='desc',
            instructor=instructor,
            is_published=True
        )
        chapter = Chapter.objects.create(course=course, title='Chapter')
        lesson1 = Lesson.objects.create(chapter=chapter, title='Lesson 1')
        lesson2 = Lesson.objects.create(chapter=chapter, title='Lesson 2')
        enrollment = Enrollment.objects.create(user=user, course=course)
        Progress.objects.create(enrollment=enrollment, lesson=lesson1)
        Progress.objects.create(enrollment=enrollment, lesson=lesson2)
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        def complete_lesson(lesson_id):
            connection.close()
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
            return client.post('/api/learning/progresses/record/', {
                'enrollment': enrollment.id,
                'lesson': lesson_id,
                'is_completed': True
            })

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(complete_lesson, lesson1.id),
                executor.submit(complete_lesson, lesson2.id),
            ]
            for future in as_completed(futures):
                future.result()

        enrollment.refresh_from_db()
        self.assertEqual(enrollment.progress, 100.0)


class LessonViewCountTests(LearningBaseAPITest):
    """课时浏览次数测试。"""

    def test_increment_view_atomic(self):
        """增加浏览次数应使用 F() 表达式。"""
        instructor = self.create_user('viewinstructor')
        course = self.create_course(instructor)
        chapter = self.create_chapter(course)
        lesson = self.create_lesson(chapter)

        response = self.client.post(f'/api/learning/lessons/{lesson.id}/increment_view/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lesson.refresh_from_db()
        self.assertEqual(lesson.view_count, 1)


class ResourceDownloadTests(LearningBaseAPITest):
    """学习资源下载次数测试。"""

    def test_increment_download_atomic(self):
        """增加下载次数应使用 F() 表达式。"""
        instructor = self.create_user('downloadinstructor')
        course = self.create_course(instructor)
        resource = LearningResource.objects.create(
            course=course,
            title='Test Resource',
            file_type='pdf',
            file_size=1024,
            download_count=0
        )

        response = self.client.post(f'/api/learning/resources/{resource.id}/increment_download/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resource.refresh_from_db()
        self.assertEqual(resource.download_count, 1)


class ReviewRatingTests(LearningBaseAPITest):
    """课程评价评分测试。"""

    def test_create_review_updates_rating(self):
        """创建评价应更新课程平均评分。"""
        user = self.create_user('reviewuser')
        instructor = self.create_user('reviewinstructor')
        course = self.create_course(instructor)
        self.authenticate(user)

        response = self.client.post('/api/learning/reviews/', {
            'course': course.id,
            'rating': 4,
            'comment': 'Good course'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        course.refresh_from_db()
        self.assertEqual(course.average_rating, 4.0)

    def test_approve_disapprove_updates_rating(self):
        """审核通过/拒绝评价应重新计算平均评分。"""
        user = self.create_user('reviewuser2')
        admin = self.create_user('reviewadmin', is_staff=True)
        instructor = self.create_user('reviewinstructor2')
        course = self.create_course(instructor)
        review = Review.objects.create(user=user, course=course, rating=5, comment='Great', is_approved=False)
        Review.objects.create(user=instructor, course=course, rating=3, comment='OK')
        self.authenticate(admin)

        response = self.client.post(f'/api/learning/reviews/{review.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        course.refresh_from_db()
        self.assertEqual(course.average_rating, 4.0)

        response = self.client.post(f'/api/learning/reviews/{review.id}/disapprove/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        course.refresh_from_db()
        self.assertEqual(course.average_rating, 3.0)


class PaymentOrderTests(LearningBaseAPITest):
    """课程支付订单测试。"""

    def setUp(self):
        super().setUp()
        self.user = self.create_user('orderuser')
        self.instructor = self.create_user('orderinstructor')
        self.paid_course = self.create_course(
            self.instructor, title='Paid Course', is_free=False, price='99.00'
        )
        self.authenticate(self.user)

    def test_create_order_for_paid_course(self):
        """付费课程可创建待支付订单，重复创建返回同一订单。"""
        response = self.client.post('/api/learning/orders/', {'course': self.paid_course.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], PaymentOrder.STATUS_PENDING)
        self.assertEqual(str(response.data['amount']), '99.00')
        self.assertTrue(response.data['order_no'].startswith('ORD'))

        again = self.client.post('/api/learning/orders/', {'course': self.paid_course.id})
        self.assertEqual(again.status_code, status.HTTP_200_OK)
        self.assertEqual(again.data['id'], response.data['id'])
        self.assertEqual(PaymentOrder.objects.count(), 1)

    def test_free_course_cannot_create_order(self):
        """免费课程不允许创建支付订单。"""
        free_course = self.create_course(
            self.instructor, title='Free Course', is_free=True, price='0.00'
        )
        response = self.client.post('/api/learning/orders/', {'course': free_course.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pay_order_enrolls_user(self):
        """支付成功后应完成报名并初始化学习进度。"""
        chapter = self.create_chapter(self.paid_course)
        self.create_lesson(chapter, title='Lesson 1')
        order = PaymentOrder.objects.create(
            user=self.user, course=self.paid_course, amount=self.paid_course.price
        )

        response = self.client.post(f'/api/learning/orders/{order.id}/pay/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, PaymentOrder.STATUS_PAID)
        self.assertIsNotNone(order.paid_at)
        enrollment = Enrollment.objects.get(user=self.user, course=self.paid_course)
        self.assertEqual(enrollment.progresses.count(), 1)
        self.paid_course.refresh_from_db()
        self.assertEqual(self.paid_course.enroll_count, 1)

        # 已支付订单不能再次支付
        again = self.client.post(f'/api/learning/orders/{order.id}/pay/')
        self.assertEqual(again.status_code, status.HTTP_400_BAD_REQUEST)

    def test_enrolled_user_cannot_create_order(self):
        """已报名用户不能重复下单。"""
        Enrollment.objects.create(user=self.user, course=self.paid_course)
        response = self.client.post('/api/learning/orders/', {'course': self.paid_course.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_pending_order(self):
        """待支付订单可取消。"""
        order = PaymentOrder.objects.create(
            user=self.user, course=self.paid_course, amount=self.paid_course.price
        )
        response = self.client.post(f'/api/learning/orders/{order.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, PaymentOrder.STATUS_CANCELLED)


class CertificateTests(LearningBaseAPITest):
    """课程证书测试。"""

    def setUp(self):
        super().setUp()
        self.user = self.create_user('certuser')
        self.other = self.create_user('certother')
        self.admin = self.create_user('certadmin', is_staff=True)
        self.instructor = self.create_user('certinstructor')
        self.course = self.create_course(self.instructor)
        self.chapter = self.create_chapter(self.course)
        self.lesson = self.create_lesson(self.chapter)

    def _create_enrollment(self):
        enrollment = Enrollment.objects.create(user=self.user, course=self.course)
        Progress.objects.create(enrollment=enrollment, lesson=self.lesson)
        return enrollment

    def test_complete_enrollment_issues_certificate(self):
        """完成课程应自动发放证书。"""
        enrollment = self._create_enrollment()
        self.authenticate(self.user)

        response = self.client.post(f'/api/learning/enrollments/{enrollment.id}/complete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        certificate = Certificate.objects.get(enrollment=enrollment)
        self.assertEqual(response.data['certificate_id'], certificate.id)
        self.assertEqual(certificate.status, Certificate.STATUS_VALID)
        self.assertTrue(certificate.number.startswith('CERT-'))

        # 重复完成不会重复发证
        self.client.post(f'/api/learning/enrollments/{enrollment.id}/complete/')
        self.assertEqual(Certificate.objects.filter(enrollment=enrollment).count(), 1)

    def test_progress_completion_issues_certificate(self):
        """学完全部课时应自动结业并发放证书。"""
        enrollment = self._create_enrollment()
        self.authenticate(self.user)

        response = self.client.post('/api/learning/progresses/record/', {
            'enrollment': enrollment.id,
            'lesson': self.lesson.id,
            'is_completed': True,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        enrollment.refresh_from_db()
        self.assertTrue(enrollment.is_completed)
        self.assertEqual(enrollment.progress, 100.0)
        self.assertTrue(Certificate.objects.filter(enrollment=enrollment).exists())

    def test_verify_certificate_public(self):
        """证书编号可公开校验。"""
        enrollment = self._create_enrollment()
        self.authenticate(self.user)
        self.client.post(f'/api/learning/enrollments/{enrollment.id}/complete/')
        certificate = Certificate.objects.get(enrollment=enrollment)

        self.client.credentials()
        response = self.client.get('/api/learning/certificates/verify/', {'number': certificate.number})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['number'], certificate.number)
        self.assertEqual(response.data['course_title'], self.course.title)

        missing = self.client.get('/api/learning/certificates/verify/')
        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_user_cannot_view_certificate(self):
        """其他用户不能查看他人证书。"""
        enrollment = self._create_enrollment()
        self.authenticate(self.user)
        self.client.post(f'/api/learning/enrollments/{enrollment.id}/complete/')
        certificate = Certificate.objects.get(enrollment=enrollment)

        self.authenticate(self.other)
        listing = self.client.get('/api/learning/certificates/')
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data['count'], 0)

        detail = self.client.get(f'/api/learning/certificates/{certificate.id}/')
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_revoke_certificate(self):
        """管理员可撤销证书。"""
        enrollment = self._create_enrollment()
        self.authenticate(self.user)
        self.client.post(f'/api/learning/enrollments/{enrollment.id}/complete/')
        certificate = Certificate.objects.get(enrollment=enrollment)

        self.authenticate(self.admin)
        response = self.client.post(
            f'/api/learning/certificates/{certificate.id}/revoke/',
            {'remark': '违规'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        certificate.refresh_from_db()
        self.assertEqual(certificate.status, Certificate.STATUS_REVOKED)
        self.assertIsNotNone(certificate.revoked_at)
