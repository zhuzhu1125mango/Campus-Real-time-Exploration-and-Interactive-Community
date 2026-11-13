"""
统一 ViewSet 基类，解决后端 API 层在权限控制、限流控制、查询集优化等方面的重复代码问题。

设计原则：
1. 通过配置化字典（permission_config / throttle_config）声明 action 级策略，避免手写 if/else。
2. 通过声明式字段（select_related_fields / prefetch_related_fields / annotation_fields）复用 N+1 优化。
3. 基类只封装通用行为，业务特定过滤仍由子类 get_queryset 负责（通过 super().get_queryset() 复用优化）。
4. 保持与原 viewsets.ModelViewSet 完全兼容，子类可按需覆盖。
"""

from rest_framework import viewsets, permissions
from rest_framework.pagination import PageNumberPagination

from users.permissions import IsOwnerOrAdmin
from users.throttles import SearchThrottle, WriteThrottle


class StandardResultsSetPagination(PageNumberPagination):
    """标准分页类。"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    通用 ModelViewSet 基类，提供配置化的权限、限流与查询集优化能力。

    子类通过覆写以下类属性即可定制行为：
      - permission_config: dict[str, list[Permission]]
      - throttle_config: dict[str, list[Throttle]]
      - select_related_fields: list[str]
      - prefetch_related_fields: list[str]
      - annotation_fields: dict[str, Expression]

    注意：permission_config / throttle_config 中存储的是**类**而非实例，
          get_permissions / get_throttles 会在运行时实例化。
    """

    # 默认配置：公开读取，认证写入，所有者/管理员可修改/删除
    permission_config = {
        'list': [permissions.AllowAny],
        'retrieve': [permissions.AllowAny],
        'create': [permissions.IsAuthenticated],
        'update': [permissions.IsAuthenticated, IsOwnerOrAdmin],
        'partial_update': [permissions.IsAuthenticated, IsOwnerOrAdmin],
        'destroy': [permissions.IsAuthenticated, IsOwnerOrAdmin],
    }

    # 默认配置：不对任何 action 施加限流，避免在迁移时意外改变原有行为。
    # 子类如需限流，可在 throttle_config 中为特定 action 配置限流类。
    throttle_config = {}

    # 查询集优化配置，子类直接声明字段名即可
    select_related_fields = []
    prefetch_related_fields = []
    annotation_fields = {}

    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        """根据 permission_config 返回当前 action 对应的权限实例列表。"""
        configured = self.permission_config.get(self.action)
        if configured is not None:
            return [permission_class() for permission_class in configured]
        return super().get_permissions()

    def get_throttles(self):
        """根据 throttle_config 返回当前 action 对应的限流实例列表。"""
        configured = self.throttle_config.get(self.action)
        if configured is not None:
            return [throttle_class() for throttle_class in configured]
        return super().get_throttles()

    def get_queryset(self):
        """
        返回查询集并应用统一的 select_related / prefetch_related / annotate 优化。

        子类如需业务过滤，应调用 ``queryset = super().get_queryset()`` 作为起点，
        再追加过滤条件，以继承基类声明的优化配置。
        """
        queryset = super().get_queryset()

        if self.select_related_fields:
            queryset = queryset.select_related(*self.select_related_fields)

        if self.prefetch_related_fields:
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)

        if self.annotation_fields:
            queryset = queryset.annotate(**self.annotation_fields)

        return queryset


class PublicReadOnlyModelViewSet(BaseModelViewSet):
    """
    公开只读 ViewSet 基类。

    list / retrieve 对匿名用户开放，写入操作需登录，修改/删除需所有者或管理员。
    """
    permission_config = {
        'list': [permissions.AllowAny],
        'retrieve': [permissions.AllowAny],
        'create': [permissions.IsAuthenticated],
        'update': [permissions.IsAuthenticated, IsOwnerOrAdmin],
        'partial_update': [permissions.IsAuthenticated, IsOwnerOrAdmin],
        'destroy': [permissions.IsAuthenticated, IsOwnerOrAdmin],
    }


class AuthenticatedModelViewSet(BaseModelViewSet):
    """
    全认证 ViewSet 基类。

    所有操作均需登录；读取无需对象级权限，写入需所有者或管理员。
    """
    permission_config = {
        'list': [permissions.IsAuthenticated],
        'retrieve': [permissions.IsAuthenticated],
        'create': [permissions.IsAuthenticated],
        'update': [permissions.IsAuthenticated, IsOwnerOrAdmin],
        'partial_update': [permissions.IsAuthenticated, IsOwnerOrAdmin],
        'destroy': [permissions.IsAuthenticated, IsOwnerOrAdmin],
    }


class AdminModelViewSet(BaseModelViewSet):
    """
    管理员专用 ViewSet 基类。

    所有操作（包括未在 permission_config 中声明的自定义 action）默认仅管理员可执行。
    """
    permission_config = {
        'list': [permissions.IsAdminUser],
        'retrieve': [permissions.IsAdminUser],
        'create': [permissions.IsAdminUser],
        'update': [permissions.IsAdminUser],
        'partial_update': [permissions.IsAdminUser],
        'destroy': [permissions.IsAdminUser],
    }

    def get_permissions(self):
        """未命中配置时默认使用管理员权限，确保自定义 action 不会意外开放。"""
        configured = self.permission_config.get(self.action)
        if configured is not None:
            return [permission_class() for permission_class in configured]
        return [permissions.IsAdminUser()]
