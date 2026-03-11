from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

def send_verification_email(email, code):
    """
    发送验证码邮件
    """
    subject = '验证您的邮箱'
    message = f'您的验证码是: {code}，10分钟内有效。'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    
    send_mail(
        subject,
        message,
        from_email,
        recipient_list,
        fail_silently=False,
    )
    
def send_password_reset_email(email, code):
    """
    发送密码重置邮件
    """
    subject = '重置您的密码'
    message = f'您的密码重置验证码是: {code}，10分钟内有效。'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    
    send_mail(
        subject,
        message,
        from_email,
        recipient_list,
        fail_silently=False,
    )