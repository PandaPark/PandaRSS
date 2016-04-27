#!/usr/bin/env python
#coding=utf-8
import decimal
import time
import random
import datetime
import calendar

random_generator = random.SystemRandom()

class Utils:
    """ 工具模块类
    """
    _base_id = 0
    _CurrentID = random_generator.randrange(1, 1024)


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

    @staticmethod
    def gen_order_id():
        if Utils._base_id >= 9999:Utils._base_id=0
        Utils._base_id += 1
        _num = str(Utils._base_id).zfill(4)
        return datetime.datetime.now().strftime("%Y%m%d%H%M%S") + _num

    @staticmethod
    def add_months(dt,months, days=0):
        month = dt.month - 1 + months
        year = dt.year + month / 12
        month = month % 12 + 1
        day = min(dt.day,calendar.monthrange(year,month)[1])
        dt = dt.replace(year=year, month=month, day=day)
        return dt + datetime.timedelta(days=days)

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
        if key in self.cache:
            return self.get(key)
        elif fetchfunc:
            expire = kwargs.pop('expire',600)
            result = fetchfunc(*args,**kwargs)
            if result:
                self.set(key,result,expire=expire)
            return result

memcache = MemCache()

