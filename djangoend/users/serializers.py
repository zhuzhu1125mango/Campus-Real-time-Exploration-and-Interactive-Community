from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta
import re

from .models import UserProfile, VerificationCode
from .sms import send_verification_sms
from .email import send_verification_email

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """用户基本信息序列化器"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'avatar', 'banner', 'bio', 
                  'is_student', 'grade', 'major', 'school', 'is_verified',
                  'date_joined', 'last_login')
        read_only_fields = ('id', 'date_joined', 'last_login', 'is_verified')


class UserProfileSerializer(serializers.ModelSerializer):
    """用户详细资料序列化器"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ('user', 'interests', 'target_schools', 'target_majors',
                  'gpa', 'study_status', 'website', 'social_links')


class UserRegisterSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    code = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password', 'password_confirm',
                  'is_student', 'code')
        extra_kwargs = {
            'email': {'required': False},
            'phone': {'required': False},
        }
    
    def validate(self, attrs):
        # 验证密码
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "两次密码不匹配。"})
        
        # 验证邮箱或手机至少提供一个
        if not attrs.get('email') and not attrs.get('phone'):
            raise serializers.ValidationError({"error": "邮箱和手机号必须至少提供一个。"})
        
        # 验证手机号格式
        if attrs.get('phone') and not re.match(r'^1[3-9]\d{9}$', attrs['phone']):
            raise serializers.ValidationError({"phone": "请输入有效的手机号。"})
        
        # 验证验证码
        if 'code' in attrs and attrs['code']:
            code = attrs['code']
            
            if attrs.get('email'):
                email = attrs['email']
                try:
                    verification = VerificationCode.objects.get(
                        email=email,
                        code=code,
                        code_type='email',
                        is_used=False
                    )
                except VerificationCode.DoesNotExist:
                    raise serializers.ValidationError({"code": "验证码无效。"})
                
                if verification.is_expired:
                    raise serializers.ValidationError({"code": "验证码已过期。"})
                
                verification.is_used = True
                verification.save()
            
            elif attrs.get('phone'):
                phone = attrs['phone']
                try:
                    verification = VerificationCode.objects.get(
                        phone=phone,
                        code=code,
                        code_type='phone',
                        is_used=False
                    )
                except VerificationCode.DoesNotExist:
                    raise serializers.ValidationError({"code": "验证码无效。"})
                
                if verification.is_expired:
                    raise serializers.ValidationError({"code": "验证码已过期。"})
                
                verification.is_used = True
                verification.save()
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        if 'code' in validated_data:
            validated_data.pop('code')
            
        user = User.objects.create_user(**validated_data)
        
        # 如果提供了验证码，则标记用户为已验证
        user.is_verified = True
        user.save()
        
        # 创建关联的用户资料
        UserProfile.objects.create(user=user)
        
        return user


class EmailVerificationSerializer(serializers.Serializer):
    """邮箱验证序列化器"""
    email = serializers.EmailField(required=True)
    purpose = serializers.ChoiceField(
        choices=['register', 'login', 'reset_password'],
        default='register'
    )
    
    def validate_email(self, value):
        purpose = self.initial_data.get('purpose', 'register')
        
        # 注册时检查邮箱是否已被注册
        if purpose == 'register' and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("该邮箱已被注册。")
            
        # 登录或重置密码时检查邮箱是否存在
        if purpose in ['login', 'reset_password'] and not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("该邮箱未注册。")
            
        return value
    
    def create(self, validated_data):
        import random
        
        email = validated_data.get('email')
        purpose = validated_data.get('purpose', 'register')
        
        # 生成6位数验证码
        code = str(random.randint(100000, 999999))
        
        # 根据用途确定code_type
        code_type = 'email'
        if purpose == 'reset_password':
            code_type = 'password'
        
        # 创建验证码记录
        verification = VerificationCode.objects.create(
            code=code,
            email=email,
            code_type=code_type,
            expires_at=timezone.now() + timedelta(minutes=10)  # 10分钟有效期
        )
        
        # 发送验证邮件
        send_verification_email(email, code)
        
        return verification


class PhoneVerificationSerializer(serializers.Serializer):
    """手机验证序列化器"""
    phone = serializers.CharField(required=True)
    purpose = serializers.ChoiceField(
        choices=['register', 'login', 'reset_password'],
        default='register'
    )
    
    def validate_phone(self, value):
        # 验证手机号格式
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError("请输入有效的手机号。")
        
        purpose = self.initial_data.get('purpose', 'register')
        
        # 注册时检查手机号是否已被注册
        if purpose == 'register' and User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("该手机号已被注册。")
            
        # 登录或重置密码时检查手机号是否存在
        if purpose in ['login', 'reset_password'] and not User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("该手机号未注册。")
        
        return value
    
    def create(self, validated_data):
        import random
        
        phone = validated_data.get('phone')
        purpose = validated_data.get('purpose', 'register')
        
        # 生成6位数验证码
        code = str(random.randint(100000, 999999))
        
        # 根据用途确定code_type
        code_type = 'phone'
        if purpose == 'reset_password':
            code_type = 'password'
        
        # 创建验证码记录
        verification = VerificationCode.objects.create(
            code=code,
            phone=phone,
            code_type=code_type,
            expires_at=timezone.now() + timedelta(minutes=10)  # 10分钟有效期
        )
        
        # 发送短信验证码
        send_verification_sms(phone, code)
        
        return verification


class VerifyCodeSerializer(serializers.Serializer):
    """验证码验证序列化器"""
    code = serializers.CharField(required=True)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    code_type = serializers.ChoiceField(
        choices=['email', 'phone', 'password'],
        default='email'
    )
    
    def validate(self, attrs):
        code = attrs.get('code')
        email = attrs.get('email')
        phone = attrs.get('phone')
        code_type = attrs.get('code_type')
        
        if not email and not phone:
            raise serializers.ValidationError("邮箱或手机号必须提供一个。")
        
        # 查找验证码记录
        filter_kwargs = {'code': code, 'is_used': False, 'code_type': code_type}
        if email:
            filter_kwargs['email'] = email
        else:
            filter_kwargs['phone'] = phone
        
        try:
            verification = VerificationCode.objects.get(**filter_kwargs)
        except VerificationCode.DoesNotExist:
            raise serializers.ValidationError("验证码无效。")
        
        # 检查是否过期
        if verification.is_expired:
            raise serializers.ValidationError("验证码已过期。")
        
        # 标记为已使用
        verification.is_used = True
        verification.save()
        
        # 对于登录和密码重置，获取用户信息
        user = None
        if email:
            user = User.objects.filter(email=email).first()
        elif phone:
            user = User.objects.filter(phone=phone).first()
        
        attrs['user'] = user
        return attrs


class UserLoginSerializer(serializers.Serializer):
    """用户登录序列化器"""
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        phone = attrs.get('phone')
        password = attrs.get('password')
        
        if not username and not email and not phone:
            raise serializers.ValidationError("用户名、邮箱或手机号必须提供一个。")
        
        # 根据提供的凭据查找用户
        filter_kwargs = {}
        if username:
            filter_kwargs['username'] = username
        elif email:
            filter_kwargs['email'] = email
        else:
            filter_kwargs['phone'] = phone
        
        try:
            user = User.objects.get(**filter_kwargs)
        except User.DoesNotExist:
            raise serializers.ValidationError("用户不存在。")
        
        # 验证密码
        if not user.check_password(password):
            raise serializers.ValidationError("密码错误。")
        
        if not user.is_active:
            raise serializers.ValidationError("该账号已被禁用。")
        
        attrs['user'] = user
        return attrs


class EmailCodeLoginSerializer(serializers.Serializer):
    """邮箱验证码登录序列化器"""
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        code = attrs.get('code')
        
        # 验证邮箱是否存在
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("该邮箱未注册。")
        
        # 验证验证码
        try:
            verification = VerificationCode.objects.get(
                email=email,
                code=code,
                code_type='email',
                is_used=False
            )
        except VerificationCode.DoesNotExist:
            raise serializers.ValidationError("验证码无效。")
        
        # A检查是否过期
        if verification.is_expired:
            raise serializers.ValidationError("验证码已过期。")
        
        # 标记为已使用
        verification.is_used = True
        verification.save()
        
        if not user.is_active:
            raise serializers.ValidationError("该账号已被禁用。")
        
        attrs['user'] = user
        return attrs


class PhoneCodeLoginSerializer(serializers.Serializer):
    """手机验证码登录序列化器"""
    phone = serializers.CharField(required=True)
    code = serializers.CharField(required=True)
    
    def validate(self, attrs):
        phone = attrs.get('phone')
        code = attrs.get('code')
        
        # 验证手机号是否存在
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError("该手机号未注册。")
        
        # 验证验证码
        try:
            verification = VerificationCode.objects.get(
                phone=phone,
                code=code,
                code_type='phone',
                is_used=False
            )
        except VerificationCode.DoesNotExist:
            raise serializers.ValidationError("验证码无效。")
        
        # 检查是否过期
        if verification.is_expired:
            raise serializers.ValidationError("验证码已过期。")
        
        # 标记为已使用
        verification.is_used = True
        verification.save()
        
        if not user.is_active:
            raise serializers.ValidationError("该账号已被禁用。")
        
        attrs['user'] = user
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    """重置密码序列化器"""
    code = serializers.CharField(required=True)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        code = attrs.get('code')
        email = attrs.get('email')
        phone = attrs.get('phone')
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        
        if not email and not phone:
            raise serializers.ValidationError("邮箱或手机号必须提供一个。")
        
        # 验证密码
        if new_password != confirm_password:
            raise serializers.ValidationError({"password": "两次密码不匹配。"})
        
        # 查找验证码记录
        filter_kwargs = {'code': code, 'is_used': False, 'code_type': 'password'}
        if email:
            filter_kwargs['email'] = email
            user_filter = {'email': email}
        else:
            filter_kwargs['phone'] = phone
            user_filter = {'phone': phone}
        
        try:
            verification = VerificationCode.objects.get(**filter_kwargs)
        except VerificationCode.DoesNotExist:
            raise serializers.ValidationError("验证码无效。")
        
        # 检查是否过期
        if verification.is_expired:
            raise serializers.ValidationError("验证码已过期。")
        
        # 标记为已使用
        verification.is_used = True
        verification.save()
        
        # 获取用户
        try:
            user = User.objects.get(**user_filter)
        except User.DoesNotExist:
            raise serializers.ValidationError("用户不存在。")
        
        attrs['user'] = user
        return attrs
    
    def save(self, **kwargs):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user