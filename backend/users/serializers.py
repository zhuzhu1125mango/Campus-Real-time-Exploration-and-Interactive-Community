import logging
import re
from datetime import timedelta

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

from .models import UserProfile, VerificationCode, PointsRecord
from .sms import send_verification_sms
from .email import send_verification_email

logger = logging.getLogger(__name__)
User = get_user_model()


class UserPublicSerializer(serializers.ModelSerializer):
    """用户公开信息序列化器，不暴露邮箱、手机号等敏感字段"""
    favorite_schools = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'avatar', 'banner', 'bio',
                  'is_student', 'grade', 'major', 'school', 'is_verified',
                  'favorite_schools', 'date_joined')
        read_only_fields = ('id', 'date_joined', 'is_verified', 'favorite_schools')

    def get_favorite_schools(self, obj):
        """从通用收藏模型中返回用户收藏的学校ID列表"""
        from django.contrib.contenttypes.models import ContentType
        from schools.models import School
        from users.favorites import Favorite
        school_ct = ContentType.objects.get_for_model(School)
        return list(
            Favorite.objects.filter(
                user=obj, content_type=school_ct
            ).order_by('-created_at').values_list('object_id', flat=True)
        )


class UserSerializer(serializers.ModelSerializer):
    """用户基本信息序列化器（本人或管理员可见完整字段）"""
    favorite_schools = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'avatar', 'banner', 'bio',
                  'is_student', 'grade', 'major', 'school', 'is_verified',
                  'favorite_schools', 'date_joined', 'last_login')
        read_only_fields = ('id', 'date_joined', 'last_login', 'is_verified', 'favorite_schools')

    def get_favorite_schools(self, obj):
        """从通用收藏模型中返回用户收藏的学校ID列表"""
        from django.contrib.contenttypes.models import ContentType
        from schools.models import School
        from users.favorites import Favorite
        school_ct = ContentType.objects.get_for_model(School)
        return list(
            Favorite.objects.filter(
                user=obj, content_type=school_ct
            ).order_by('-created_at').values_list('object_id', flat=True)
        )


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
        self.context['code_verified'] = False
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
                self.context['code_verified'] = True

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
                self.context['code_verified'] = True

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        if 'code' in validated_data:
            validated_data.pop('code')

        user = User.objects.create_user(**validated_data)

        # 仅当验证码校验通过后才标记用户为已验证
        if self.context.get('code_verified'):
            user.is_verified = True
            user.save(update_fields=['is_verified'])

        # 创建关联的用户资料，处理可能的重复创建问题
        try:
            UserProfile.objects.create(user=user)
        except Exception:
            # 如果UserProfile已经存在，则忽略错误
            pass

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
        
        # 开发环境记录验证码到调试日志，生产环境必须接入真实邮件服务
        # send_verification_email(email, code)
        logger.debug(f"邮箱验证码已生成：{code}，收件人：{email}")
        
        return verification


class PhoneVerificationSerializer(serializers.Serializer):
    """手机验证序列化器"""
    phone = serializers.CharField(required=True)
    purpose = serializers.ChoiceField(
        choices=['register', 'login', 'reset_password'],
        default='register'
    )
    
    def validate_phone(self, value):
        # 去除前后空白字符，避免用户输入或粘贴时带入空格导致查询失败
        value = value.strip()
        
        # 验证手机号格式
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError("请输入有效的手机号。")
        
        purpose = self.initial_data.get('purpose', 'register')
        user_exists = User.objects.filter(phone=value).exists()
        logger.debug(f"手机号校验: phone={value}, purpose={purpose}, user_exists={user_exists}")
        
        # 注册时检查手机号是否已被注册
        if purpose == 'register' and user_exists:
            raise serializers.ValidationError("该手机号已被注册。")
            
        # 登录或重置密码时检查手机号是否存在
        if purpose in ['login', 'reset_password'] and not user_exists:
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
        
        # 开发环境记录验证码到调试日志，生产环境必须接入真实短信服务
        # send_verification_sms(phone, code)
        logger.debug(f"手机验证码已生成：{code}，手机号：{phone}")
        
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
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        code = attrs.get('code')
        email = attrs.get('email')
        phone = attrs.get('phone')
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if not email and not phone:
            raise serializers.ValidationError("邮箱或手机号必须提供一个。")
        
        # 验证密码
        if password != password_confirm:
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
        user.set_password(self.validated_data['password'])
        user.save()
        return user


class PointsRecordSerializer(serializers.ModelSerializer):
    """积分记录序列化器"""
    class Meta:
        model = PointsRecord
        fields = ('id', 'action', 'points', 'description', 'created_at')
        read_only_fields = ('id', 'created_at')