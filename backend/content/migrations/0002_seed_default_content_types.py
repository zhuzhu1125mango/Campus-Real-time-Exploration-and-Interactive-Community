from django.db import migrations


def seed_default_content_types(apps, schema_editor):
    ContentType = apps.get_model('content', 'ContentType')
    defaults = [
        {'name': '文章', 'description': '图文内容', 'is_active': True},
        {'name': '视频', 'description': '视频内容', 'is_active': True},
        {'name': '资讯', 'description': '校园资讯', 'is_active': True},
        {'name': '经验', 'description': '学习/生活经验分享', 'is_active': True},
    ]
    for item in defaults:
        ContentType.objects.get_or_create(name=item['name'], defaults=item)


def reverse_seed(apps, schema_editor):
    ContentType = apps.get_model('content', 'ContentType')
    ContentType.objects.filter(name__in=['文章', '视频', '资讯', '经验']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_default_content_types, reverse_seed),
    ]
