"""清理未被内容引用的富文本图片。"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from content.models import Content, ContentImage


class Command(BaseCommand):
    help = '删除创建超过指定天数且未被任何内容富文本引用的图片'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7, help='保留天数，默认 7 天')
        parser.add_argument('--dry-run', action='store_true', help='仅扫描并输出结果，不实际删除')

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        cutoff = timezone.now() - timedelta(days=days)

        candidates = ContentImage.objects.filter(created_at__lt=cutoff).order_by('created_at')
        self.stdout.write(f'扫描到超过 {days} 天的图片 {candidates.count()} 张')

        removed = 0
        for content_image in candidates:
            url = content_image.image.url
            name = content_image.image.name
            if Content.objects.filter(Q(content__contains=url) | Q(content__contains=name)).exists():
                continue

            removed += 1
            if dry_run:
                self.stdout.write(f'[dry-run] 待删除图片：{name}')
                continue

            storage = content_image.image.storage
            content_image.delete()
            if storage.exists(name):
                storage.delete(name)

        action = '待删除' if dry_run else '已删除'
        self.stdout.write(self.style.SUCCESS(f'{action}图片 {removed} 张'))
