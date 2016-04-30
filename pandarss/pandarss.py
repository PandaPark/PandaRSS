#!/usr/bin/env python
#coding=utf-8

import os
import sys
import json
import time
import bottle
import logging
import decimal
import datetime
import functools
from hashlib import md5
from bottle import (
    static_file,template, Bottle, run,abort,error,
    request, response,redirect
)
from utils import Utils,memcache
from trapi import TrApi
from alipay import AliPay,Settings


logger = logging.getLogger('pandarss')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(u'%(asctime)s %(name)s %(levelname)-4s %(message)s','%b %d %H:%M:%S'))
logger.addHandler(handler)

app = Bottle()
app.config['system.port']  = 8080
app.config['system.template_path'] = os.path.join(os.path.dirname(__file__),'views')  

_config1 = os.path.abspath(os.path.join(os.path.dirname(__file__),'pandarss.conf'))
_config2 = '/etc/pandarss.conf'
if os.path.exists(_config2):
    print 'using config',_config2
    app.config.load_config(_config2)
elif os.path.exists(_config1):
    print 'using config',_config1
    app.config.load_config(_config1)

bottle.TEMPLATE_PATH.insert(0, app.config['system.template_path'])
trapi = TrApi(app)
alipay = AliPay(Settings(
    ALIPAY_KEY = app.config['alipay.alipay_key'],
    ALIPAY_INPUT_CHARSET = 'utf-8',
    # 合作身份者ID，以2088开头的16位纯数字
    ALIPAY_PARTNER = app.config['alipay.alipay_partner'],
    # 签约支付宝账号或卖家支付宝帐户
    ALIPAY_SELLER_EMAIL = app.config['alipay.alipay_seller_email'],
    ALIPAY_SIGN_TYPE = 'MD5',
    # 付完款后跳转的页面（同步通知） 要用 http://格式的完整路径，不允许加?id=123这类自定义参数
    ALIPAY_RETURN_URL=app.config['alipay.alipay_return_url'],
    # 交易过程中服务器异步通知的页面 要用 http://格式的完整路径，不允许加?id=123这类自定义参数
    ALIPAY_NOTIFY_URL=app.config['alipay.alipay_notify_url'],
    ALIPAY_SHOW_URL='',
    # 访问模式,根据自己的服务器是否支持ssl访问，若支持请选择https；若不支持请选择http
    ALIPAY_TRANSPORT='https'
),logger=logger)

################################################################################
# web appliocation
################################################################################

def get_cookie(name):
    return request.get_cookie(md5(name).hexdigest(),secret=app.config['system.session_secret'])
        
def set_cookie(name,value,**options):
    response.set_cookie(md5(name).hexdigest(),value,secret=app.config['system.session_secret'],**options)

def chklogin(func):
    @functools.wraps(func)
    def warp(*args,**kargs):
        return get_cookie("username") and func(*args,**kargs) or redirect('/')
    return warp

def render(name,*args,**kwargs):
    kwargs.update(utils=Utils,account_number=get_cookie("username"))
    return template(name,*args,**kwargs) 

@app.error(400)
def abort400(error):
    return template('error',errmsg=error.body)

@app.route('/imgs/<filename:path>')
def statc_img(filename):
    return static_file(filename, root='%s/imgs'%app.config['system.template_path'])


@app.route('/css/<filename:path>')
def static_css(filename):
    return static_file(filename, root='%s/css'%app.config['system.template_path'])

@app.route('/js/<filename:path>')
def static_js(filename):
    return static_file(filename, root='%s/js'%app.config['system.template_path'])


@app.post('/login')
def do_login():
    username = request.params.get('username')
    password = request.params.get('password')
    login_resp = trapi.customer_auth(username,password)
    if login_resp['code'] > 0:
        return abort(400,login_resp['msg'])
    else:
        set_cookie('username',username)
        set_cookie("customer_name",login_resp['customer_name'])
        redirect("/")

@app.route('/logout')
def do_logout():
    set_cookie('username','')
    set_cookie("customer_name",'')
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
    chkresp = trapi.customer_auth(account_number,oldpassword)
    if chkresp['code']>1:
        return abort(400,u'旧密码校验失败:%s'%chkresp['msg'])
    apiresp = trapi.update_password(account_number,newpassword1)
    if apiresp['code'] > 0:
        return abort(400,apiresp['msg'])
    else:
        return render('message',msg=u'修改密码成功')

@app.route('/account',apply=chklogin)
def account():
    customer_name = get_cookie('customer_name')
    apiresp = trapi.customer_query(customer_name)
    get_product = lambda pid:memcache.aget('product_cache_%s'%pid,trapi.product_get,pid,expire=600) or {}
    if apiresp['code'] > 0:
        return abort(400,apiresp['msg'])
    else:
        return render('account',
            get_product=get_product,
            customer=apiresp['customer'],
            accounts=apiresp['accounts'])

@app.route('/orders',apply=chklogin)
def orders():
    customer_name = get_cookie('customer_name')
    apiresp = trapi.order_query(customer_name)
    get_product = lambda pid:memcache.aget('product_cache_%s'%pid,trapi.product_get,pid,expire=600)
    if apiresp['code'] > 0:
        return abort(400,apiresp['msg'])
    else:
        return render('orders',get_product=get_product,orders=apiresp['orders'])


################################################################################
# customer order new
################################################################################

@app.route('/product/order')
def new_order():
    #payfunc(utils.gen_order_id(),product['product_name'],product['product_name'],utils.fen2yuan(product['fee_price']))
    product_id = request.params.get('product_id')
    product = trapi.product_get(product_id)
    node_resp = trapi.node_list()
    if node_resp['code'] > 0:
        return abort(400,node_resp['msg'])
    account = trapi.account_gen()
    return render('order_form',product=product,nodes=node_resp['nodes'],account=account)


@app.post('/product/corder')
def confirm_order():
    rundata = dict(
        product_id = request.params.get('product_id'),
        node_id = request.params.get('node_id'),
        node = trapi.node_get(request.params.get('node_id')),
        realname = request.params.get('realname'),
        email = request.params.get('email'),
        idcard = request.params.get('idcard'),
        mobile = request.params.get('mobile'),
        address = request.params.get('address'),
        account_number = request.params.get('account_number'),
        password = request.params.get('password'),
        months = request.params.get('months'),
        begin_date = datetime.datetime.now().strftime("%Y-%m-%d") 
    )
    product = trapi.product_get(rundata['product_id'])

    if product['product_policy'] == 0:
        order_fee = decimal.Decimal(product['fee_price']) * decimal.Decimal(rundata['months'])
        order_fee = int(order_fee.to_integral_value())
        rundata['fee_total'] =  Utils.fen2yuan(order_fee)
        expire_date = Utils.add_months(datetime.datetime.now(),int(rundata['months']))
        expire_date = expire_date.strftime( "%Y-%m-%d")
        rundata['expire_date'] = expire_date
    elif product['product_policy'] == 2:
        rundata['fee_total'] = Utils.fen2yuan(product['fee_price'])
        expire_date = Utils.add_months(datetime.datetime.now(),int(product['fee_months']))
        expire_date = expire_date.strftime( "%Y-%m-%d")
        rundata['expire_date'] = expire_date

    return render('order_cform',product=product,rundata=rundata)

@app.post('/product/order/alipay')
def alipay_order():
    addresp = trapi.customer_add(
        request.params.get('account_number'), 
        request.params.get('password'), 
        request.params.get('product_id'), 
        request.params.get('realname'), 
        request.params.get('email'), 
        request.params.get('node_id'), 
        request.params.get('idcard'), 
        request.params.get('mobile'), 
        request.params.get('address'), 
        request.params.get('begin_date'), 
        request.params.get('expire_date'), 
        request.params.get('fee_value'), '0',
        balance='0.00',
        time_length = '0',
        flow_length = '0')
    if addresp['code'] > 0:
        return abort(400,addresp['msg'])
    else:
        order_id = addresp['order_id']
        product = trapi.product_get(request.params.get('product_id'))
        url = alipay.create_direct_pay_by_user(order_id, product['product_name'], product['product_name'], request.params.get('fee_value'))
        redirect(url)


################################################################################
# alipay order verify
################################################################################
@app.post('/order/verify')
def verify_order():
    params = request.params
    isok = alipay.notify_verify(params)
    if isok:
        apiresp = trapi.customer_payok(order_id=params.get('out_trade_no'))
        if apiresp['code'] > 0:
            logger.info(apiresp['msg'])
            return abort(400,apiresp['msg'])
        return 'success'
    else:
        logger.info(u"订单无效")
        return abort(400,u"订单无效")


@app.route('/alipay/return')
def alipay_return():
    order_id = request.params.get('out_trade_no')
    apiresp = trapi.order_query(order_id=order_id)
    account = None
    if apiresp['code'] > 0:
        logger.info(apiresp['msg'])
    else:
        order = apiresp.get('order')
        if order:
            account = order.get("account_number")
    return render('alipay_return',params=request.params,account=account)


@app.route('/product')
def product():
    apiresp = trapi.product_list()
    if apiresp['code'] > 0:
        return abort(400,apiresp['msg'])
    else:
        products=(p for p in apiresp['products'] if p['product_policy'] not in [6])
        return render('product',products=products,payfunc=alipay.create_direct_pay_by_user)

################################################################################
# application running
################################################################################




def main():
    host = app.config['system.host']
    port = int(app.config['system.port'])
    run(app,host=host, port=port, debug=True,reloader=False)

def txrun():
    host = app.config['system.host']
    port = int(app.config['system.port'])
    run(app,host=host, port=port, debug=True,reloader=False,server='twisted')

if __name__ == '__main__':
    logger.debug("start pandarss")
    main()









