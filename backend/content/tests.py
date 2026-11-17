"""内容模块测试。

覆盖可见性、创建与修订、审核状态机、评论计数与通知、个人内容列表、举报与图片上传清理。
"""

import os
import shutil
import tempfile
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from notifications.models import Notification

from .models import (
    Category, Comment, Content, ContentImage, ContentLike, ContentReport,
    ContentRevision, ContentType, Tag,
)

User = get_user_model()


class ContentAPITests(TestCase):
    """内容接口测试。"""

    def setUp(self):
        cache.clear()
        self.alice = User.objects.create_user(username='alice', password='testpass', email='alice@example.com')
        self.bob = User.objects.create_user(username='bob', password='testpass', email='bob@example.com')
        self.admin = User.objects.create_user(
            username='admin', password='testpass', email='admin@example.com', is_staff=True
        )

        self.content_type, _ = ContentType.objects.get_or_create(name='文章')
        self.category = Category.objects.create(name='校园')
        self.tag = Tag.objects.create(name='攻略')

        self.published = Content.objects.create(
            title='已发布文章',
            slug='published-post',
            content_type=self.content_type,
            category=self.category,
            author=self.alice,
            content='<p>正文</p>',
            status='published',
        )
        self.draft = Content.objects.create(
            title='草稿文章',
            slug='draft-post',
            content_type=self.content_type,
            author=self.alice,
            content='<p>草稿</p>',
            status='draft',
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.alice)

        self.contents_url = '/api/content/contents/'
        self.comments_url = '/api/content/comments/'

        self.points_patcher = patch('content.views.queue_update_user_points')
        self.mock_points = self.points_patcher.start()
        self.addCleanup(self.points_patcher.stop)

    def test_anonymous_list_only_published(self):
        """游客只能看到已发布内容。"""
        self.client.force_authenticate(user=None)

        response = self.client.get(self.contents_url)

        self.assertEqual(response.status_code, 200)
        statuses = {item['status'] for item in response.data['results']}
        self.assertEqual(statuses, {'published'})

    def test_author_sees_own_draft_in_list(self):
        """作者能在列表中看到自己的草稿。"""
        response = self.client.get(self.contents_url)

        self.assertEqual(response.status_code, 200)
        titles = {item['title'] for item in response.data['results']}
        self.assertEqual(titles, {'已发布文章', '草稿文章'})

    def test_other_user_cannot_retrieve_draft(self):
        """他人无法访问未发布内容。"""
        self.client.force_authenticate(user=self.bob)

        response = self.client.get(f'{self.contents_url}{self.draft.id}/')

        self.assertEqual(response.status_code, 404)

    def test_author_can_retrieve_own_draft(self):
        """作者可以访问自己的草稿。"""
        response = self.client.get(f'{self.contents_url}{self.draft.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], '草稿文章')

    def test_create_content_generates_slug_and_revision(self):
        """创建内容应生成 slug、写入修订记录并清洗 HTML。"""
        response = self.client.post(
            self.contents_url,
            {
                'title': 'Hello World',
                'content_type': self.content_type.id,
                'category': self.category.id,
                'tags': [self.tag.id],
                'content': '<p>正文</p><script>alert(1)</script>',
                'summary': '<b>摘要</b>',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)

        content = Content.objects.get(slug='hello-world')
        self.assertEqual(content.author, self.alice)
        self.assertEqual(content.status, 'draft')
        self.assertNotIn('<script', content.content)
        self.assertEqual(content.revisions.count(), 1)

        self.mock_points.assert_called_once()
        self.assertEqual(self.mock_points.call_args.args[1], 'post')

    def test_create_content_keeps_custom_slug(self):
        """自定义 slug 应被保留。"""
        response = self.client.post(
            self.contents_url,
            {
                'title': '另一篇文章',
                'slug': 'custom-slug',
                'content_type': self.content_type.id,
                'content': '<p>正文</p>',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Content.objects.filter(slug='custom-slug').exists())

    def test_create_content_requires_authentication(self):
        """未登录用户不能创建内容。"""
        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.contents_url,
            {
                'title': '匿名文章',
                'content_type': self.content_type.id,
                'content': '<p>正文</p>',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 401)

    def test_update_content_creates_revision(self):
        """更新内容应追加修订记录。"""
        response = self.client.patch(
            f'{self.contents_url}{self.published.id}/',
            {'title': '已发布文章（更新）'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.published.refresh_from_db()
        self.assertEqual(self.published.title, '已发布文章（更新）')
        self.assertEqual(ContentRevision.objects.filter(content=self.published).count(), 1)

    def test_other_user_cannot_update_content(self):
        """非作者不能修改他人内容。"""
        self.client.force_authenticate(user=self.bob)

        response = self.client.patch(
            f'{self.contents_url}{self.published.id}/',
            {'title': '恶意修改'},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        self.published.refresh_from_db()
        self.assertEqual(self.published.title, '已发布文章')

    def test_submit_sets_pending(self):
        """作者提交审核后状态变为 pending。"""
        response = self.client.post(f'{self.contents_url}{self.draft.id}/submit/')

        self.assertEqual(response.status_code, 200)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, 'pending')

    def test_non_author_cannot_submit(self):
        """非作者不能提交他人内容审核。"""
        self.client.force_authenticate(user=self.bob)

        response = self.client.post(f'{self.contents_url}{self.published.id}/submit/')

        self.assertEqual(response.status_code, 403)
        self.published.refresh_from_db()
        self.assertEqual(self.published.status, 'published')

    def test_admin_approve_publishes_content(self):
        """管理员审核通过后内容变为已发布。"""
        self.draft.status = 'pending'
        self.draft.save()

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f'{self.contents_url}{self.draft.id}/approve/')

        self.assertEqual(response.status_code, 200)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, 'published')
        self.assertTrue(self.draft.is_published)
        self.assertIsNotNone(self.draft.publish_date)

    def test_non_admin_cannot_approve(self):
        """普通用户不能审核内容。"""
        response = self.client.post(f'{self.contents_url}{self.draft.id}/approve/')

        self.assertEqual(response.status_code, 403)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, 'draft')

    def test_comment_create_updates_count_and_notifies_author(self):
        """评论内容应更新评论数并通知作者。"""
        self.client.force_authenticate(user=self.bob)

        response = self.client.post(
            self.comments_url,
            {'content': self.published.id, 'content_text': '很有帮助'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.published.refresh_from_db()
        self.assertEqual(self.published.comment_count, 1)

        notification = Notification.objects.get(recipient=self.alice)
        self.assertEqual(notification.notification_type, 'content_comment')
        self.assertEqual(notification.title, '新评论')

    def test_comment_on_own_content_creates_no_notification(self):
        """评论自己的内容不产生通知。"""
        response = self.client.post(
            self.comments_url,
            {'content': self.published.id, 'content_text': '补充说明'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notification.objects.count(), 0)

    def test_comment_create_requires_authentication(self):
        """未登录用户不能评论。"""
        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.comments_url,
            {'content': self.published.id, 'content_text': '匿名评论'},
            format='json',
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(Comment.objects.count(), 0)

    def test_comment_list_filters_by_content(self):
        """评论列表支持按内容过滤，且只返回已通过审核的评论。"""
        other_content = Content.objects.create(
            title='另一篇已发布文章',
            slug='another-post',
            content_type=self.content_type,
            author=self.alice,
            content='<p>正文</p>',
            status='published',
        )
        Comment.objects.create(content=self.published, user=self.bob, content_text='第一条')
        Comment.objects.create(content=other_content, user=self.bob, content_text='第二条')
        Comment.objects.create(
            content=self.published, user=self.bob, content_text='待审核', is_approved=False
        )

        response = self.client.get(self.comments_url, {'content': self.published.id})

        self.assertEqual(response.status_code, 200)
        texts = [item['content_text'] for item in response.data['results']]
        self.assertEqual(texts, ['第一条'])

    def test_admin_disapprove_decrements_comment_count(self):
        """管理员驳回评论后内容评论数减一。"""
        comment = Comment.objects.create(
            content=self.published, user=self.bob, content_text='待驳回'
        )
        Content.objects.filter(pk=self.published.pk).update(comment_count=1)

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f'{self.comments_url}{comment.id}/disapprove/')

        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertFalse(comment.is_approved)

        self.published.refresh_from_db()
        self.assertEqual(self.published.comment_count, 0)

    def test_like_content_increments_and_awards_points(self):
        """点赞内容应落库、更新计数并发放双方积分。"""
        self.client.force_authenticate(user=self.bob)

        response = self.client.post(f'{self.contents_url}{self.published.id}/like/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'liked')

        self.published.refresh_from_db()
        self.assertEqual(self.published.like_count, 1)
        self.assertTrue(
            ContentLike.objects.filter(content=self.published, user=self.bob).exists()
        )
        self.mock_points.assert_any_call(self.bob.id, 'like', description='点赞内容')
        self.mock_points.assert_any_call(self.alice.id, 'liked', description='内容被点赞')

    def test_like_content_twice_returns_400(self):
        """重复点赞返回 400 且计数只增加一次。"""
        self.client.force_authenticate(user=self.bob)

        first = self.client.post(f'{self.contents_url}{self.published.id}/like/')
        second = self.client.post(f'{self.contents_url}{self.published.id}/like/')

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 400)
        self.published.refresh_from_db()
        self.assertEqual(self.published.like_count, 1)

    def test_like_own_content_skips_author_reward_and_notification(self):
        """点赞自己的内容不发放被赞积分，也不产生通知。"""
        response = self.client.post(f'{self.contents_url}{self.published.id}/like/')

        self.assertEqual(response.status_code, 200)
        self.mock_points.assert_called_once_with(self.alice.id, 'like', description='点赞内容')
        self.assertEqual(Notification.objects.count(), 0)

    def test_like_notifies_author(self):
        """点赞他人内容应通知作者。"""
        self.client.force_authenticate(user=self.bob)

        self.client.post(f'{self.contents_url}{self.published.id}/like/')

        notification = Notification.objects.get(recipient=self.alice)
        self.assertEqual(notification.sender, self.bob)
        self.assertEqual(notification.notification_type, 'interaction')
        self.assertEqual(notification.title, '新点赞')

    def test_unlike_content(self):
        """取消点赞应删除记录并递减计数。"""
        self.client.force_authenticate(user=self.bob)
        self.client.post(f'{self.contents_url}{self.published.id}/like/')

        response = self.client.post(f'{self.contents_url}{self.published.id}/unlike/')

        self.assertEqual(response.status_code, 200)
        self.published.refresh_from_db()
        self.assertEqual(self.published.like_count, 0)
        self.assertFalse(
            ContentLike.objects.filter(content=self.published, user=self.bob).exists()
        )

    def test_unlike_without_like_returns_400(self):
        """未点赞时取消点赞返回 400。"""
        response = self.client.post(f'{self.contents_url}{self.published.id}/unlike/')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['status'], 'not_liked')

    def test_list_marks_is_liked_for_current_user(self):
        """列表中的 is_liked 反映当前用户的点赞状态。"""
        ContentLike.objects.create(content=self.published, user=self.bob)

        self.client.force_authenticate(user=self.bob)
        response = self.client.get(self.contents_url)

        item = next(
            row for row in response.data['results'] if row['id'] == self.published.id
        )
        self.assertTrue(item['is_liked'])

    def test_my_contents_returns_only_own(self):
        """个人内容列表只返回当前用户的内容。"""
        Content.objects.create(
            title='bob 的文章',
            slug='bob-post',
            content_type=self.content_type,
            author=self.bob,
            content='<p>正文</p>',
            status='published',
        )

        response = self.client.get(f'{self.contents_url}my_contents/')

        self.assertEqual(response.status_code, 200)
        titles = {item['title'] for item in response.data['results']}
        self.assertEqual(titles, {'已发布文章', '草稿文章'})


GIF_BYTES = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff'
    b'!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


def make_gif(name='tiny.gif'):
    return SimpleUploadedFile(name, GIF_BYTES, content_type='image/gif')


class ContentReportAPITests(TestCase):
    """内容举报接口测试。"""

    def setUp(self):
        cache.clear()
        self.reporter = User.objects.create_user(
            username='reporter', password='testpass', email='reporter@example.com'
        )
        self.other = User.objects.create_user(
            username='other', password='testpass', email='other@example.com'
        )
        self.admin = User.objects.create_user(
            username='report-admin', password='testpass', email='admin@example.com', is_staff=True
        )
        self.content_type = ContentType.objects.create(name='举报测试类型')
        self.content = Content.objects.create(
            title='被举报内容',
            slug='reported-content',
            content_type=self.content_type,
            author=self.other,
            content='<p>正文</p>',
            status='published',
        )
        self.reports_url = '/api/content/reports/'
        self.client = APIClient()
        self.client.force_authenticate(user=self.reporter)

    def test_report_content_success(self):
        """登录用户举报内容成功，举报记录状态为待处理。"""
        response = self.client.post(
            f'/api/content/contents/{self.content.id}/report/',
            {'reason': 'spam', 'description': '广告内容'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'pending')

        report = ContentReport.objects.get(pk=response.data['id'])
        self.assertEqual(report.content, self.content)
        self.assertEqual(report.reporter, self.reporter)
        self.assertEqual(report.reason, 'spam')
        self.assertEqual(report.status, 'pending')

    def test_report_same_content_twice_returns_400(self):
        """同一用户重复举报同一内容返回 400。"""
        self.client.post(
            f'/api/content/contents/{self.content.id}/report/', {'reason': 'spam'}, format='json'
        )

        response = self.client.post(
            f'/api/content/contents/{self.content.id}/report/', {'reason': 'abuse'}, format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], '您已举报过该内容')
        self.assertEqual(ContentReport.objects.filter(content=self.content).count(), 1)

    def test_report_requires_authentication(self):
        """未登录用户不能举报。"""
        self.client.force_authenticate(user=None)

        response = self.client.post(
            f'/api/content/contents/{self.content.id}/report/', {'reason': 'spam'}, format='json'
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(ContentReport.objects.count(), 0)

    def test_non_admin_cannot_list_reports(self):
        """普通用户访问举报列表返回 403。"""
        response = self.client.get(self.reports_url)

        self.assertEqual(response.status_code, 403)

    def test_admin_list_reports_with_status_filter(self):
        """管理员可查看举报列表并按状态筛选。"""
        ContentReport.objects.create(content=self.content, reporter=self.reporter, reason='spam')
        handled = ContentReport.objects.create(
            content=self.content, reporter=self.other, reason='abuse', status='handled'
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.reports_url, {'status': 'handled'})

        self.assertEqual(response.status_code, 200)
        ids = [item['id'] for item in response.data['results']]
        self.assertEqual(ids, [handled.id])

        item = response.data['results'][0]
        self.assertEqual(item['content'], self.content.title)
        self.assertEqual(item['reporter'], {'id': self.other.id, 'username': self.other.username})

    def test_admin_handle_and_reject_reports(self):
        """管理员处理/驳回举报后状态与处理人落库。"""
        first = ContentReport.objects.create(content=self.content, reporter=self.reporter, reason='spam')
        second = ContentReport.objects.create(content=self.content, reporter=self.other, reason='abuse')

        self.client.force_authenticate(user=self.admin)

        handled_response = self.client.post(f'{self.reports_url}{first.id}/handle/')
        rejected_response = self.client.post(f'{self.reports_url}{second.id}/reject/')

        self.assertEqual(handled_response.status_code, 200)
        self.assertEqual(handled_response.data['status'], 'handled')
        self.assertEqual(rejected_response.status_code, 200)
        self.assertEqual(rejected_response.data['status'], 'rejected')

        first.refresh_from_db()
        self.assertEqual(first.status, 'handled')
        self.assertEqual(first.handled_by, self.admin)
        self.assertIsNotNone(first.handled_at)

        second.refresh_from_db()
        self.assertEqual(second.status, 'rejected')
        self.assertEqual(second.handled_by, self.admin)
        self.assertIsNotNone(second.handled_at)


class ContentImageUploadAPITests(TestCase):
    """富文本图片上传接口测试。"""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='uploader', password='testpass', email='uploader@example.com'
        )
        self.media_root = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.upload_url = '/api/content/images/'

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_upload_gif_success(self):
        """登录用户上传图片成功并返回 url。"""
        response = self.client.post(
            self.upload_url, {'image': make_gif()}, format='multipart'
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn('/media/content/images/', response.data['url'])
        self.assertTrue(ContentImage.objects.filter(pk=response.data['id']).exists())

    def test_upload_non_image_rejected(self):
        """非图片文件返回 400。"""
        upload = SimpleUploadedFile('note.txt', b'hello world', content_type='text/plain')

        response = self.client.post(self.upload_url, {'image': upload}, format='multipart')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ContentImage.objects.count(), 0)

    def test_upload_too_large_rejected(self):
        """超过 5MB 的图片返回 400。"""
        big = SimpleUploadedFile(
            'big.gif', b'GIF89a' + b'\x00' * (5 * 1024 * 1024), content_type='image/gif'
        )

        response = self.client.post(self.upload_url, {'image': big}, format='multipart')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ContentImage.objects.count(), 0)

    def test_upload_requires_authentication(self):
        """未登录用户不能上传图片。"""
        self.client.force_authenticate(user=None)

        response = self.client.post(self.upload_url, {'image': make_gif()}, format='multipart')

        self.assertEqual(response.status_code, 401)
        self.assertEqual(ContentImage.objects.count(), 0)


class CleanupContentImagesCommandTests(TestCase):
    """清理未被引用图片的管理命令测试。"""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='cleaner', password='testpass', email='cleaner@example.com'
        )
        self.media_root = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.content_type = ContentType.objects.create(name='清理测试类型')
        self.content = Content.objects.create(
            title='引用图片的内容',
            slug='cleanup-content',
            content_type=self.content_type,
            author=self.user,
            content='<p>占位</p>',
        )

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _create_image(self, name):
        return ContentImage.objects.create(uploader=self.user, image=make_gif(name))

    def test_deletes_only_unreferenced_old_images(self):
        """仅删除未被内容引用且创建超过 N 天的图片。"""
        referenced = self._create_image('referenced.gif')
        self.content.content = f'<p><img src="{referenced.image.url}" alt="引用"></p>'
        self.content.save()

        unreferenced = self._create_image('unreferenced.gif')

        old_time = timezone.now() - timedelta(days=5)
        ContentImage.objects.filter(pk__in=[referenced.pk, unreferenced.pk]).update(created_at=old_time)

        referenced_path = referenced.image.path
        unreferenced_path = unreferenced.image.path

        call_command('cleanup_content_images', days=1)

        self.assertTrue(ContentImage.objects.filter(pk=referenced.pk).exists())
        self.assertFalse(ContentImage.objects.filter(pk=unreferenced.pk).exists())
        self.assertTrue(os.path.exists(referenced_path))
        self.assertFalse(os.path.exists(unreferenced_path))
