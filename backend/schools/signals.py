from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import School


@receiver(post_save, sender=School)
def create_school_board(sender, instance, created, **kwargs):
    """创建学校时自动创建对应的论坛板块"""
    if not created:
        return

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
        school=instance,
        defaults={
            'name': f'{instance.name}论坛',
            'description': f'欢迎来到{instance.name}论坛，这里是校友交流、分享资讯的地方。',
            'category': category,
            'icon': 'el-icon-school',
            'order': 0
        }
    )
