from bottle import route, run
from bottle import static_file,template
import os
import bottle


TEMPDIR = os.path.join(os.path.dirname(__file__),'views')
IMGDIR = os.path.join(os.path.dirname(__file__),'view/simgs')
CSSDIR = os.path.join(os.path.dirname(__file__),'views/css')
JSDIR = os.path.join(os.path.dirname(__file__),'views/js')
bottle.TEMPLATE_PATH.insert(0, TEMPDIR)

@route('/imgs/<filename:path>')
def send_image(filename):
    return static_file(filename, root=IMGDIR)


@route('/css/<filename:path>')
def send_image(filename):
    return static_file(filename, root=CSSDIR)


@route('/js/<filename:path>')
def send_image(filename):
    return static_file(filename, root=JSDIR)

@route('/')
def index():
    return template('index', name='hello')

@route('/password')
def password():
    return template('password', name='hello')


@route('/account')
def account():
    return template('account', name='hello')


run(host='localhost', port=8080, debug=True,reload=True)









