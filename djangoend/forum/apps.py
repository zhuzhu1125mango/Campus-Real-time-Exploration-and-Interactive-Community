from django.apps import AppConfig


class ForumConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'forum'
    verbose_name = '论坛'

    def ready(self):
        try:
            import forum.signals  # noqa
        except ImportError:
            pass
