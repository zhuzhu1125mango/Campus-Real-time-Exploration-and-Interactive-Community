import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# 检查并创建测试用户
if not User.objects.filter(username='testuser').exists():
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='Testpass123!'
    )
    print('Test user created successfully')
else:
    print('Test user already exists')

# 检查管理员用户
if User.objects.filter(username='admin').exists():
    print('Admin user already exists')
else:
    print('Admin user not found')

# 显示所有用户
print('\nAll users:')
for user in User.objects.all():
    print(f'Username: {user.username}, Email: {user.email}, Is admin: {user.is_superuser}')