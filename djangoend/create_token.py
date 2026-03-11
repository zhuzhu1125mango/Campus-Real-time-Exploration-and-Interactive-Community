import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

# 为所有用户创建Token
for user in User.objects.all():
    token, created = Token.objects.get_or_create(user=user)
    status = "创建" if created else "已存在"
    print(f"用户 {user.username} (ID: {user.id}) 的Token {status}: {token.key}") 