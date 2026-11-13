from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = 'notifications'
    verbose_name = '通知管理'

    def ready(self):
        import notifications.signals
