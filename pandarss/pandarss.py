#!/usr/bin/env python
#coding=utf-8

import os
import json
import time
import bottle
import urllib  
import urllib2  
import logging
import decimal
import functools
from hashlib import md5
from bottle import (
    static_file,template, Bottle, run,abort,error,
    request, response,redirect
)

logger = logging.getLogger('pandarss')

app = Bottle()
app.config['template_path'] = os.path.join(os.path.dirname(__file__),'views')  
app.config['api_url'] = 'http://127.0.0.1:1816/api/v1'
app.config['api_key'] = '0BOTrVO6WRtkRnKTmM52nKfQpvCGY8vD'
app.config['session_secret'] = '3DQ5qhmYiB44Q1YIDLVyVUdEqFvgVKLW'
bottle.TEMPLATE_PATH.insert(0, app.config['template_path'])

class Utils:
    """ 工具模块类
    """
    @staticmethod
    def fen2yuan(fen=0):
        f = decimal.Decimal(fen or 0)
        y = f / decimal.Decimal(100)
        return str(y.quantize(decimal.Decimal('1.00')))

    @staticmethod
    def yuan2fen(yuan=0):
        y = decimal.Decimal(yuan or 0)
        f = y * decimal.Decimal(100)
        return int(f.to_integral_value())

    @staticmethod
    def kb2mb(ik):
        _kb = decimal.Decimal(ik or 0)
        _mb = _kb / decimal.Decimal(1024)
        return str(_mb.quantize(decimal.Decimal('1.00')))

    @staticmethod
    def sec2hour(sec=0):
        _sec = decimal.Decimal(sec or 0)
        _hor = _sec / decimal.Decimal(3600)
        return str(_hor.quantize(decimal.Decimal('1.00')))

    @staticmethod
    def bps2mbps(bps):
        _bps = decimal.Decimal(bps or 0)
        _mbps = _bps / decimal.Decimal(1024*1024)
        return str(_mbps.quantize(decimal.Decimal('1.00')))

class MemCache:
    ''' 内存缓存
    '''
    def __init__(self):
        self.cache = {}

    def set(self, key, obj, expire=0):
        if obj in ("", None) or key in ("", None):
            return None
        objdict = dict(obj=obj,expire=expire,time=time.time())
        self.cache[key] = objdict

    def get(self, key):
        if key in self.cache:
            objdict = self.cache[key]
            _time = time.time()
            if objdict['expire'] == 0 or (_time - objdict['time']) < objdict['expire']:
                return objdict['obj']
            else:
                del self.cache[key]
                return None
        else:
            return None

    def aget(self, key, fetchfunc, *args, **kwargs):
        result = self.get(key)
        if result:
            return result
        if fetchfunc:
            expire = kwargs.pop('expire',600)
            result = fetchfunc(*args,**kwargs)
            if result:
                self.set(key,result,expire=expire)
            return result

memcache = MemCache()

class TrApi:
    ''' toughradius v2 api 封装
    '''
    @staticmethod
    def apirequest(apipath,**params):
        try:
            api_req = { k:v for k,v in params.iteritems() if k not in ('sign')}
            api_req['nonce'] = str(time.time())
            _args = [p.decode('utf-8') for p in api_req.values() if p is not None]
            _args.sort()
            _args.insert(0, app.config['api_key'])
            api_req['sign'] = md5((''.join(_args)).encode('utf-8')).hexdigest().upper()
            response = urllib2.urlopen(
                urllib2.Request('{0}{1}'.format(app.config['api_url'],apipath),urllib.urlencode(api_req)))  
            return json.loads(response.read())
        except:
            import traceback
            traceback.print_exc()
            return dict(code=99999,msg='unknow error')

    @staticmethod
    def customer_auth(account_number,password):
        return TrApi.apirequest('/customer/auth',account_number=account_number,password=password)

    @staticmethod
    def customer_query(account_number):
        return TrApi.apirequest('/customer/query',account_number=account_number)

    @staticmethod
    def update_password(account_number,password):
        return TrApi.apirequest('/account/pw/update',account_number=account_number,password=password)

    @staticmethod
    def product_list():
        return TrApi.apirequest('/product/query')

    @staticmethod
    def product_get(product_id):
        products = []
        apiresp = TrApi.apirequest('/product/query',product_id=str(product_id))
        if apiresp['code'] == 0:
            products = apiresp['products']
        return products and products[0] or {}


#### web application

def get_cookie(name):
    return request.get_cookie(md5(name).hexdigest(),secret=app.config['session_secret'])
        
def set_cookie(name,value,**options):
    response.set_cookie(md5(name).hexdigest(),value,secret=app.config['session_secret'],**options)

def chklogin(func):
    @functools.wraps(func)
    def warp(*args,**kargs):
        return get_cookie("username") and func(*args,**kargs) or redirect('/')
    return warp

def render(name,*args,**kwargs):
    return template(name,*args,
        account_number=get_cookie("username"),
        utils=Utils,
        **kwargs
    ) 

@app.error(400)
def abort400(error):
    return template('error',errmsg=error.body)

@app.route('/imgs/<filename:path>')
def statc_img(filename):
    return static_file(filename, root='%s/imgs'%app.config['template_path'])


@app.route('/css/<filename:path>')
def static_css(filename):
    return static_file(filename, root='%s/css'%app.config['template_path'])


@app.route('/js/<filename:path>')
def static_js(filename):
    return static_file(filename, root='%s/js'%app.config['template_path'])


@app.post('/login')
def do_login():
    username = request.params.get('username')
    password = request.params.get('password')
    login_resp = TrApi.customer_auth(username,password)
    if login_resp['code'] > 0:
        return abort(400,login_resp['msg'])
    else:
        set_cookie('username',username)
        redirect("/")

@app.route('/logout')
def do_logout():
    set_cookie('username','')
    request.cookies.clear()
    redirect("/")

@app.route('/')
def index():
    account_number = get_cookie('username')
    return render('index')

@app.get('/password',apply=chklogin)
def password():
    return render('password',spec_account_number=request.params.get('account_number'))

@app.post('/password',apply=chklogin)
def do_password():
    account_number = request.params.get('spec_account_number')
    oldpassword = request.params.get('oldpassword')
    newpassword1 = request.params.get('newpassword1')
    newpassword2 = request.params.get('newpassword2')
    if newpassword1 not in [newpassword2]:
        return abort(400,u"确认密码不匹配")
    chkresp = TrApi.customer_auth(account_number,oldpassword)
    if chkresp['code']>1:
        return abort(400,u'旧密码校验失败:%s'%chkresp['msg'])
    apiresp = TrApi.update_password(account_number,newpassword1)
    if apiresp['code'] > 0:
        return abort(400,apiresp['msg'])
    else:
        return render('message',msg=u'修改密码成功')

@app.route('/account',apply=chklogin)
def account():
    account_number = get_cookie('username')
    apiresp = TrApi.customer_query(account_number)
    get_product = lambda pid:memcache.aget('product_cache_%s'%pid,TrApi.product_get,pid,expire=600)
    if apiresp['code'] > 0:
        return abort(400,apiresp['msg'])
    else:
        return render('account',
            get_product=get_product,
            customer=apiresp['customer'],
            accounts=apiresp['accounts'])

@app.route('/product',apply=chklogin)
def product():
    apiresp = TrApi.product_list()
    if apiresp['code'] > 0:
        return abort(400,apiresp['msg'])
    else:
        products=(p for p in apiresp['products'] if p['product_policy'] not in [6])
        return render('product',products=products)

def load_config():
    _config1 = os.path.join(os.path.dirname(__file__),'pandarss.json')
    _config2 = '/etc/pandarss.json'
    if os.path.exists(_config2):
        app.config.load_config(_config2)
    elif os.path.exists(_config1):
        app.config.load_config(_config1)

def main():
    load_config()
    run(app,host='localhost', port=8080, debug=True,reloader=False)

if __name__ == '__main__':
    main()









