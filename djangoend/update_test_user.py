import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# 更新测试用户
try:
    user = User.objects.get(username='testuser')
    user.email = 'test@example.com'
    user.set_password('Testpass123!')
    user.save()
    print('Test user updated successfully')
    print(f'Username: {user.username}, Email: {user.email}, Is admin: {user.is_superuser}')
except User.DoesNotExist:
    print('Test user not found')