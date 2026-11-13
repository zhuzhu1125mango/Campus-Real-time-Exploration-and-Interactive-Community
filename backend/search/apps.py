from django.apps import AppConfig


class SearchConfig(AppConfig):
    name = 'search'

    def ready(self):
        # 导入信号处理器
        import search.signals  # noqa: F401

        # 初始化 elasticsearch-dsl 默认连接
        try:
            from search.documents import setup_elasticsearch_connections
            setup_elasticsearch_connections()
        except Exception:
            # 开发环境未启动 ES 时不阻断 Django 启动
            import logging
            logging.getLogger(__name__).warning("Elasticsearch 连接初始化失败，搜索将降级到数据库")
