#!/usr/bin/env python
#coding=utf-8
import time
import json
import urllib  
import urllib2  
from hashlib import md5

class TrApi:
    ''' toughradius v2 api 封装
    '''

    def __init__(self,app):
        self.app = app

    def apirequest(self,apipath,**params):
        try:
            api_req = { k:v for k,v in params.iteritems() if k not in ('sign')}
            api_req['nonce'] = str(time.time())
            _args = [p.decode('utf-8') for p in api_req.values() if p is not None]
            _args.sort()
            _args.insert(0, self.app.config['system.api_key'])
            api_req['sign'] = md5((''.join(_args)).encode('utf-8')).hexdigest().upper()
            _api_url = '{0}{1}'.format(self.app.config['system.api_url'],apipath)
            print _api_url
            response = urllib2.urlopen(urllib2.Request(_api_url,urllib.urlencode(api_req)))  
            return json.loads(response.read())
        except:
            import traceback
            traceback.print_exc()
            return dict(code=99999,msg='unknow error')

    def customer_auth(self,account_number,password):
        return self.apirequest('/customer/auth',account_number=account_number,password=password)

    def account_query(self,account_number):
        return self.apirequest('/account/query',account_number=account_number)

    def account_renew(self,order_id,account_number='',expire_date='',fee_value='',pay_status=None):
        return self.apirequest('/account/renew',
            order_id=order_id,
            account_number=account_number,
            expire_date=expire_date,
            fee_value=fee_value,
            pay_status=pay_status
        )

    def customer_add(self,account_number,password,product_id,
        realname,email,node_id,idcard,mobile,address,begin_date,expire_date,fee_value,pay_status,**kwargs):
        return self.apirequest('/customer/add',
            realname=realname,
            email=email,
            account_number=account_number,
            password=password,
            node_id=node_id,
            product_id=product_id,
            idcard=idcard,
            mobile=mobile,
            address=address,
            begin_date=begin_date,
            expire_date=expire_date,
            fee_value=fee_value,
            pay_status=pay_status,
            **kwargs)


    def customer_payok(self,order_id):
        return self.apirequest('/order/payok',order_id=order_id)

    def customer_query(self,customer_name):
        return self.apirequest('/customer/query',customer_name=customer_name)

    def order_query(self,customer_name='',order_id=''):
        return self.apirequest('/order/query',customer_name=customer_name,order_id=order_id)

    def update_password(self,account_number,password):
        return self.apirequest('/account/pw/update',account_number=account_number,password=password)

    def product_list(self):
        return self.apirequest('/product/query')

    def node_list(self):
        return self.apirequest('/node/query')

    def node_get(self,node_id):
        nodes = []
        apiresp = self.apirequest('/node/query',node_id=str(node_id))
        if apiresp['code'] == 0:
            nodes = apiresp['nodes']
        return nodes and nodes[0] or {}

    def product_get(self,product_id):
        products = []
        apiresp = self.apirequest('/product/query',product_id=str(product_id))
        if apiresp['code'] == 0:
            products = apiresp['products']
        return products and products[0] or {}

    def account_gen(self):
        apiresp = self.apirequest('/account/gen')
        if apiresp['code'] == 0:
            return apiresp['account']
        return ''

