from rest_framework import permissions


def _get_owner(obj, request):
    """尝试获取对象的属主；User 对象本身就是属主。"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if isinstance(obj, User):
        return obj
    return getattr(obj, 'user', None) or getattr(obj, 'author', None) or getattr(obj, 'owner', None) or getattr(obj, 'sender', None)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    对象级权限：仅资源所有者或管理员可写。
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user and request.user.is_staff:
            return True
        owner = _get_owner(obj, request)
        return owner is not None and owner == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    对象级权限：所有人可读，仅所有者或管理员可写。
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user and request.user.is_staff:
            return True
        owner = _get_owner(obj, request)
        return owner is not None and owner == request.user


class IsAdminOrModerator(permissions.BasePermission):
    """
    仅管理员或指定版主可操作。
    用于论坛主题/帖子的版主权限。
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        # 版主身份通过视图自定义逻辑判断，默认返回 True，由视图进一步校验
        return True


class IsInstructorOrAdmin(permissions.BasePermission):
    """
    仅课程讲师或管理员可操作。
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        instructor = getattr(obj, 'instructor', None)
        return instructor is not None and instructor == request.user


class IsCourseInstructorOrAdmin(permissions.BasePermission):
    """
    仅所属课程的讲师或管理员可操作（用于章节、课时、学习资源）。
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        course = getattr(obj, 'course', None)
        if course is None:
            return False
        instructor = getattr(course, 'instructor', None)
        return instructor is not None and instructor == request.user
