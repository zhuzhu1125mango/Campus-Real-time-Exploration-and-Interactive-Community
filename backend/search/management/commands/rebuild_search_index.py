"""
全量重建 Elasticsearch 搜索索引。

用法：
    uv run python manage.py rebuild_search_index [--model schools.School]
"""

from django.core.management.base import BaseCommand

from search.client import es_is_available
from search.tasks import MODEL_TO_DOC


class Command(BaseCommand):
    help = '重建 Elasticsearch 搜索索引'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            help='仅重建指定模型，例如 schools.School',
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='重建前删除已有索引',
        )

    def handle(self, *args, **options):
        if not es_is_available():
            self.stderr.write(self.style.ERROR('Elasticsearch 不可用，无法重建索引'))
            return

        model_key = options.get('model')
        delete_first = options.get('delete')

        if model_key:
            if model_key not in MODEL_TO_DOC:
                self.stderr.write(self.style.ERROR(f'未注册模型: {model_key}'))
                return
            docs_to_rebuild = {model_key: MODEL_TO_DOC[model_key]}
        else:
            docs_to_rebuild = MODEL_TO_DOC

        if delete_first:
            self.stdout.write('删除已有索引...')
            from elasticsearch_dsl import Index
            for key, (_, doc_class) in docs_to_rebuild.items():
                idx = Index(doc_class.Index.name)
                if idx.exists():
                    idx.delete()
            self.stdout.write(self.style.SUCCESS('索引已删除'))

        self.stdout.write('创建索引...')
        for _, doc_class in docs_to_rebuild.values():
            doc_class.init()
        self.stdout.write(self.style.SUCCESS('索引创建完成'))

        self.stdout.write('开始全量索引数据...')
        for app_label_model, (_, doc_class) in docs_to_rebuild.items():
            app_label, model_name = app_label_model.split('.')
            from django.apps import apps
            Model = apps.get_model(app_label, model_name)

            total = Model.objects.count()
            self.stdout.write(f'索引 {app_label_model}，共 {total} 条...')

            from search.tasks import index_object
            for pk in Model.objects.values_list('pk', flat=True).iterator():
                index_object.delay(app_label_model, pk)

        self.stdout.write(self.style.SUCCESS('全量索引任务已下发，请在 Celery Worker 中观察执行进度。'))
