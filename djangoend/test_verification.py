import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from users.serializers import EmailVerificationSerializer, PhoneVerificationSerializer, VerifyCodeSerializer
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

# 创建请求工厂
factory = APIRequestFactory()

print("测试验证码功能")
print("=" * 50)

# 测试邮箱验证码
def test_email_verification():
    print("\n1. 测试邮箱验证码")
    print("-" * 30)
    
    # 创建请求
    request = factory.post('/api/users/send_email_code/', {
        'email': 'test@example.com',
        'purpose': 'register'
    })
    
    # 实例化序列化器
    serializer = EmailVerificationSerializer(data={'email': 'test@example.com', 'purpose': 'register'}, context={'request': request})
    
    # 验证数据
    if serializer.is_valid():
        # 保存（生成验证码）
        verification = serializer.save()
        print(f"✅ 邮箱验证码生成成功: {verification.code}")
        print(f"   邮箱: {verification.email}")
        print(f"   类型: {verification.code_type}")
        print(f"   过期时间: {verification.expires_at}")
        
        # 测试验证验证码
        verify_request = factory.post('/api/users/verify_code/')
        
        verify_serializer = VerifyCodeSerializer(data={'code': verification.code, 'email': 'test@example.com', 'code_type': 'email'}, context={'request': verify_request})
        if verify_serializer.is_valid():
            print("✅ 邮箱验证码验证成功")
        else:
            print(f"❌ 邮箱验证码验证失败: {verify_serializer.errors}")
    else:
        print(f"❌ 邮箱验证码生成失败: {serializer.errors}")

# 测试手机验证码
def test_phone_verification():
    print("\n2. 测试手机验证码")
    print("-" * 30)
    
    # 创建请求
    request = factory.post('/api/users/send_phone_code/', {
        'phone': '13800138000',
        'purpose': 'register'
    })
    
    # 实例化序列化器
    serializer = PhoneVerificationSerializer(data={'phone': '13800138000', 'purpose': 'register'}, context={'request': request})
    
    # 验证数据
    if serializer.is_valid():
        # 保存（生成验证码）
        verification = serializer.save()
        print(f"✅ 手机验证码生成成功: {verification.code}")
        print(f"   手机号: {verification.phone}")
        print(f"   类型: {verification.code_type}")
        print(f"   过期时间: {verification.expires_at}")
        
        # 测试验证验证码
        verify_request = factory.post('/api/users/verify_code/')
        
        verify_serializer = VerifyCodeSerializer(data={'code': verification.code, 'phone': '13800138000', 'code_type': 'phone'}, context={'request': verify_request})
        if verify_serializer.is_valid():
            print("✅ 手机验证码验证成功")
        else:
            print(f"❌ 手机验证码验证失败: {verify_serializer.errors}")
    else:
        print(f"❌ 手机验证码生成失败: {serializer.errors}")

# 运行测试
if __name__ == "__main__":
    test_email_verification()
    test_phone_verification()
    print("\n" + "=" * 50)
    print("测试完成")