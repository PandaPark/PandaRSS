#!/usr/bin/env python
# coding=utf-8

import types
from urllib import urlencode
from hashlib import md5
import urllib2  

class Settings(dict):
    def __getattr__(self, key): 
        try:
            return self[key]
        except KeyError, k:
            raise AttributeError, k
    
    def __setattr__(self, key, value): 
        self[key] = value
    
    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError, k:
            raise AttributeError, k
    
    def __repr__(self):     
        return '<Settings ' + dict.__repr__(self) + '>'

class AliPay:

    GATEWAY = 'https://mapi.alipay.com/gateway.do?'

    def __init__(self, settings={},logger=None):
        self.settings = settings
        self.logger = logger

    def event_alipay_setup(self,settings):
        self.settings = settings

    def safestr(self, val, errors='strict'):
        encoding = self.settings.get('ALIPAY_INPUT_CHARSET','utf-8')
        if val is None:
            return ''
        if isinstance(val, unicode):
            return val.encode('utf-8',errors)
        elif isinstance(val, str):
            return val.decode('utf-8', errors).encode(encoding, errors)
        elif isinstance(val, (int,float)):
            return str(val)
        elif isinstance(val, Exception):
            return ' '.join([self.safestr(arg, encoding,errors) for arg in val])
        else:
            try:
                return str(val)
            except:
                return unicode(val).encode(encoding, errors)
        return val

    def make_sign(self, **msg):
        ks = msg.keys()
        ks.sort()
        sign_str = '&'.join([ '%s=%s'%(k,msg[k]) for k in ks ])
        if 'MD5' == self.settings.ALIPAY_SIGN_TYPE:
            return md5(sign_str + self.settings.ALIPAY_KEY).hexdigest()

        raise Exception('not support sign type %s' % settings.ALIPAY_SIGN_TYPE)


    def check_sign(self, **msg):
        if "sign" not in msg:
            return False
        params = {self.safestr(k):self.safestr(msg[k]) for k in msg if k not in ('sign','sign_type')}
        local_sign = self.make_sign(**params)
        return msg['sign'] == local_sign


    def make_request_url(self,**params):
        params.pop('sign',None)
        params.pop('sign_type',None)
        _params = {self.safestr(k):self.safestr(v) for k,v in params.iteritems() if v not in ('', None) }
        _params['sign'] = self.make_sign(**_params)
        _params['sign_type'] = self.settings.ALIPAY_SIGN_TYPE
        return AliPay.GATEWAY + urlencode(_params)


    def create_direct_pay_by_user(self, tn, subject, body, total_fee):
        params = {}
        params['service']       = 'create_direct_pay_by_user'
        params['payment_type']  = '1'
        
        # 获取配置文件
        params['partner']           = self.settings.ALIPAY_PARTNER
        params['seller_email']      = self.settings.ALIPAY_SELLER_EMAIL
        params['return_url']        = self.settings.ALIPAY_RETURN_URL
        params['notify_url']        = self.settings.ALIPAY_NOTIFY_URL
        params['_input_charset']    = self.settings.ALIPAY_INPUT_CHARSET
        params['show_url']          = self.settings.ALIPAY_SHOW_URL
        
        # 从订单数据中动态获取到的必填参数
        params['out_trade_no']  = tn        # 请与贵网站订单系统中的唯一订单号匹配
        params['subject']       = subject   # 订单名称，显示在支付宝收银台里的“商品名称”里，显示在支付宝的交易管理的“商品名称”的列表里。
        params['body']          = body      # 订单描述、订单详细、订单备注，显示在支付宝收银台里的“商品描述”里
        params['total_fee']     = total_fee # 订单总金额，显示在支付宝收银台里的“应付总额”里
        
        # 扩展功能参数——网银提前
        params['paymethod'] = 'directPay'   # 默认支付方式，四个值可选：bankPay(网银); cartoon(卡通); directPay(余额); CASH(网点支付)
        params['defaultbank'] = ''          # 默认网银代号，代号列表见http://club.alipay.com/read.php?tid=8681379
        
        # 扩展功能参数——防钓鱼
        params['anti_phishing_key'] = ''
        params['exter_invoke_ip'] = ''
        
        # 扩展功能参数——自定义参数
        params['buyer_email'] = ''
        params['extra_common_param'] = ''
        
        # 扩展功能参数——分润
        params['royalty_type'] = ''
        params['royalty_parameters'] = ''
        
        return self.make_request_url(**params)
    
    def notify_verify(self, request):
        self.logger.info(request)
        if not self.check_sign(**request):
            self.logger.error('check_sign failure')
            return False
        
        # 二级验证--查询支付宝服务器此条信息是否有效
        params = {}
        params['partner'] = self.settings.ALIPAY_PARTNER
        params['notify_id'] = request.get('notify_id', '')
        if self.settings.ALIPAY_TRANSPORT == 'https':
            params['service'] = 'notify_verify'
            gateway = 'https://mapi.alipay.com/gateway.do'
        else:
            gateway = 'http://notify.alipay.com/trade/notify_query.do'

        veryfy_result = urllib2.urlopen(urllib2.Request(gateway,urlencode(params))).read()
        self.logger.info('veryfy_result:%s'%veryfy_result)
        return veryfy_result.lower().strip() == 'true'


if __name__ == '__main__':
    settings = Settings(
        ALIPAY_KEY = '234234',
        ALIPAY_INPUT_CHARSET = 'utf-8',
        # 合作身份者ID，以2088开头的16位纯数字
        ALIPAY_PARTNER = '234',
        # 签约支付宝账号或卖家支付宝帐户
        ALIPAY_SELLER_EMAIL = 'payment@34.com',
        ALIPAY_SIGN_TYPE = 'MD5',
        # 付完款后跳转的页面（同步通知） 要用 http://格式的完整路径，不允许加?id=123这类自定义参数
        ALIPAY_RETURN_URL='',
        # 交易过程中服务器异步通知的页面 要用 http://格式的完整路径，不允许加?id=123这类自定义参数
        ALIPAY_NOTIFY_URL='',
        ALIPAY_SHOW_URL='',
        # 访问模式,根据自己的服务器是否支持ssl访问，若支持请选择https；若不支持请选择http
        ALIPAY_TRANSPORT='https'
    )
    alipay = AliPay(settings)
    params = {}
    params['service']       = 'create_direct_pay_by_user'
    params['payment_type']  = '1'
    params['aaaa'] = u"好"
    print alipay.make_request_url(**params)
    print alipay.create_direct_pay_by_user('2323525', u"阿士大夫", u"啥打法是否", 0.01)

