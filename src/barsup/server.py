# coding: utf-8
import json
import hashlib
import time
import os

import tornado
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, StaticFileHandler, Application
import tornado.websocket

import zmq
from zmq.eventloop import ioloop
from zmq.eventloop.zmqstream import ZMQStream


UID_COOKIE = 'barsup_session'
UID_POOL = {}


class MainHandler(RequestHandler):
    def initialize(self, index_path):
        self._index_path = index_path

    def get(self):
        if not self.get_cookie(UID_COOKIE):
            hash_ = hashlib.sha1(str(time.time()))
            self.set_cookie(UID_COOKIE, hash_.hexdigest())
        return self.render(os.path.join(self._index_path, "index.html"))


class WSHandler(tornado.websocket.WebSocketHandler):
    _uid = None

    def initialize(self, mq):
        self._mq_sock = mq

    def open(self):
        self._uid = self.get_cookie(UID_COOKIE)
        UID_POOL.setdefault(self._uid, set()).add(self)
        print('Connect. Cookie: %s' % self._uid)

    def on_close(self):
        conns = UID_POOL[self._uid]
        conns.remove(self)
        if conns:
            UID_POOL.pop(self._uid)
        print('Disconnect. Cookie: %s' % self._uid)

    def on_message(self, msg):
        self._mq_sock.send_json({'uid': self._uid, 'data': msg})


def on_mq_recv(msgs):
    for msg in msgs:
        msg = json.loads(msg.decode())
        uid, data = msg['uid'], msg['data']
        assert uid, "No UID in message!"

        # Временно отправка сообщений всем клиентам до тех пор,
        # # пока не будет правил привязки на основе api key
        # for _, hdls in UID_POOL.items():
        # for hdl in hdls:
        #         hdl.write_message(data)

        # Отправка сообщения в классическом режиме:
        # Кто прислал сообщение, тот и получает ответ
        hdls = UID_POOL.get(uid)
        if hdls:
            for hdl in hdls:
                hdl.write_message(data)
        else:
            print("Unknown UID:", uid)


def run(port, sock_pull, sock_push, static_root):
    """
    Запускает сервер с указанными параметрами
    """
    ioloop.install()

    zmq_context = zmq.Context()

    pull_sock = zmq_context.socket(zmq.PULL)
    pull_sock.connect(sock_pull)
    pull_stream = ZMQStream(pull_sock)
    pull_stream.on_recv(on_mq_recv)

    push_sock = zmq_context.socket(zmq.PUSH)
    push_sock.connect(sock_push)

    os.environ.setdefault('BUP_PATH', '.')
    static_path = os.path.abspath(os.path.expandvars(static_root))
    application = Application([
        (r"/$", MainHandler, {'index_path': static_path}),
        (r"/ws$", WSHandler, {'mq': push_sock}),
        (r'/(.*)', StaticFileHandler, {'path': static_path}),
    ])

    application.listen(port)
    print('Tornado starting at "%s" port' % port)
    IOLoop.instance().start()


DEFAULT_PARAMS = {
    'port': 8000,
    'sock_pull': 'tcp://localhost:3001',
    'sock_push': 'tcp://localhost:3002',
    'static_root': '$BUP_PATH/static/barsup/'
}
