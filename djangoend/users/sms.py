import json
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)

# 尝试导入阿里云SDK，如果失败则使用开发模式
try:
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkcore.request import CommonRequest
    ALIYUN_SDK_AVAILABLE = True
except ImportError:
    ALIYUN_SDK_AVAILABLE = False
    logger.warning("阿里云SDK未安装，短信功能将使用开发模式")

class AliyunSMS:
    def __init__(self):
        """初始化阿里云SMS客户端"""
        self.access_key_id = settings.ALIYUN_ACCESS_KEY_ID
        self.access_key_secret = settings.ALIYUN_ACCESS_KEY_SECRET
        self.sign_name = settings.ALIYUN_SMS_SIGN_NAME
        self.template_code = settings.ALIYUN_SMS_TEMPLATE_CODE
        self.client = AcsClient(self.access_key_id, self.access_key_secret, 'cn-hangzhou')

    def send_verification_code(self, phone, code):
        """
        发送短信验证码
        :param phone: 手机号
        :param code: 验证码
        :return: 发送结果
        """
        request = CommonRequest()
        request.set_accept_format('json')
        request.set_domain('dysmsapi.aliyuncs.com')
        request.set_method('POST')
        request.set_protocol_type('https')
        request.set_version('2017-05-25')
        request.set_action_name('SendSms')

        request.add_query_param('RegionId', "cn-hangzhou")
        request.add_query_param('PhoneNumbers', phone)
        request.add_query_param('SignName', self.sign_name)
        request.add_query_param('TemplateCode', self.template_code)

        # 设置短信模板参数
        template_param = {
            "code": code
        }
        request.add_query_param('TemplateParam', json.dumps(template_param))

        try:
            response = self.client.do_action_with_exception(request)
            response_json = json.loads(response.decode('utf-8'))
            
            if response_json.get('Code') == 'OK':
                logger.info(f"短信验证码发送成功: {phone}")
                return True, "短信验证码发送成功"
            else:
                logger.error(f"短信验证码发送失败: {phone}, 错误: {response_json}")
                return False, response_json.get('Message', '短信验证码发送失败')
        except Exception as e:
            logger.error(f"短信验证码发送异常: {phone}, 错误: {str(e)}")
            return False, str(e)


# 验证码发送函数
def send_verification_sms(phone, code):
    """
    发送验证码短信
    :param phone: 手机号
    :param code: 验证码
    :return: 发送结果
    """
    if settings.SMS_ENABLED and ALIYUN_SDK_AVAILABLE:
        sms = AliyunSMS()
        return sms.send_verification_code(phone, code)
    else:
        # 开发模式下不实际发送短信，只打印日志
        if not ALIYUN_SDK_AVAILABLE:
            logger.info(f"开发模式(无SDK): 向 {phone} 发送验证码 {code}")
        else:
            logger.info(f"开发模式: 向 {phone} 发送验证码 {code}")
        return True, "开发模式: 验证码发送成功" 