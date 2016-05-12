#PandaRSS

PandaRSS 是一个基于 ToughRADIUS V2版本 API 的自助服务系统。

## 快速指南

### 运行环境

- Linux 
- Python 2.7
- pip 
- Twisted>=15.0.0 可选
- bottle>=0.12.7

### 安装

    pip  install -U  https://github.com/lanyeit/PandaRSS/archive/master.zip

### 配置

新增加一个配置文件 /etc/pandarss.conf,内容如下

    [system]
    host = 0.0.0.0
    port = 1819
    home_site = www.mydomain.com
    api_url = http://x.x.x.x:1816/api/v1
    api_key = CRTCcMB7tfnXU8aXIyfavfuqruvXkNng
    session_secret = CRTCcMB7tfnXU8aXIyfavfuqruvXkNng

    [alipay]
    alipay_key = jrid3242fs52234scxdzqoajmww
    alipay_partner = 2342342342342
    alipay_seller_email = mypay@xxxx.com
    alipay_return_url = http://www.mydomain.com/alipay/return
    alipay_notify_url = http://www.mydomain.com/order/verify


- api_url： 请填写部署的ToughRADIUS的服务器地址，替换ip，端口即可
- api_key： 请填写部署的ToughRADIUS的安全密钥
- session_secret： 一个32位的字符串，用来做cookie加密

支付宝配置参数，请根据你的支付宝申请的直接到账支付提供的参数，要使用支付宝支付，服务器需要绑定域名，建议通过nginx等代理服务器实现。

### 运行

输入 pandarss 会直接以非守护进程模式运行，按Ctrl+C可退出。

若要以守护进程模式运行，可使用nohup命令：

    nohup pandarss &

默认的 pandarss  运行模式性能不高，可以使用基于twisted异步高性能网络框架来运行

    nohup pandarss_txrun &


### 绑定到ToughRADIUS服务运行

如果你的ToughRADIUS是以本地模式安装的，可以在ToughRADIUS的服务进程中配置pandarss进程。

修改 /etc/toughradius.conf, 加入以下内容

    [program:pandarss]
    command=pandarss_txrun
    startretries = 10
    autorestart = true
    redirect_stderr=true
    stdout_logfile=/var/toughradius/pandarss.log

这样pandarss可以随toughradius的进程启动停止。







