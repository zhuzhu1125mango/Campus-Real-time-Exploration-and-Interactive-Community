"""
用户模块上传文件验证器
"""
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _


# 允许的图片扩展名
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']

# 最大文件大小（单位：字节）
MAX_AVATAR_SIZE = 5 * 1024 * 1024   # 5MB
MAX_BANNER_SIZE = 10 * 1024 * 1024  # 10MB


def validate_image_extension(value):
    """验证图片文件扩展名"""
    validator = FileExtensionValidator(
        allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
        message=_(f"仅支持 {', '.join(ALLOWED_IMAGE_EXTENSIONS)} 格式的图片。")
    )
    validator(value)


def validate_avatar_size(value):
    """验证头像文件大小"""
    if value.size > MAX_AVATAR_SIZE:
        raise ValidationError(
            _(f"头像文件大小不能超过 {MAX_AVATAR_SIZE / 1024 / 1024:.0f}MB。")
        )


def validate_banner_size(value):
    """验证背景图文件大小"""
    if value.size > MAX_BANNER_SIZE:
        raise ValidationError(
            _(f"背景图文件大小不能超过 {MAX_BANNER_SIZE / 1024 / 1024:.0f}MB。")
        )
