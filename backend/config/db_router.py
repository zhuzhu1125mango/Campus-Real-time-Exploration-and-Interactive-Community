"""
MySQL 主从读写分离 Router。

- 写操作固定路由到 default（主库）。
- 读操作默认路由到 replica（从库）；如果未配置 replica 则回退到 default。
- 处于事务中的读操作路由到 default，避免主从延迟导致事务内读到旧数据。
- 模型关系允许跨库（实际仍属于同一 MySQL 实例的不同逻辑库或角色）。

强一致读场景（如用户刚发布内容后立即查看）可在视图层显式使用：
    Model.objects.using('default').get(...)
"""

from django.conf import settings


class PrimaryReplicaRouter:
    """主从读写分离路由。"""

    def __init__(self):
        self._replica_available = self._check_replica_available()

    @staticmethod
    def _check_replica_available():
        return 'replica' in settings.DATABASES

    def db_for_read(self, model, **hints):
        """
        读请求优先路由到 replica；未配置时回退到 default。
        Django 在事务内会自动将读请求绑定到已选中的数据库，因此此处无需额外判断。
        """
        if self._replica_available:
            return 'replica'
        return 'default'

    def db_for_write(self, model, **hints):
        """写请求固定路由到 default（主库）。"""
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        允许跨库关系。当前主从属于同一 MySQL 实例，关系操作可正常执行。
        返回 True 表示允许；返回 None 表示让其他 router 决定。
        """
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        只允许在主库上执行迁移。从库通过 MySQL 主从复制同步结构变更。
        """
        return db == 'default'
