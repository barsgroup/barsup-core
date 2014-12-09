# coding: utf-8
import json
import hashlib
import time
import os

import tornado
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, StaticFileHandler, Application, RedirectHandler
import tornado.websocket

import zmq
from zmq.eventloop import ioloop
from zmq.eventloop.zmqstream import ZMQStream


UID_COOKIE = 'barsup_session'
SESSION_POOL = {}


class MainHandler(RequestHandler):
    def initialize(self, index_path):
        self._index_path = index_path

    def get(self):
        if not self.get_cookie(UID_COOKIE):
            hash_ = hashlib.sha1(str(time.time()).encode())
            self.set_cookie(UID_COOKIE, hash_.hexdigest())
        return self.render(
            os.path.join(self._index_path, "index.html"))


class WSHandler(tornado.websocket.WebSocketHandler):
    _session_id = None

    def initialize(self, mq):
        self._mq_sock = mq

    def open(self):
        self._session_id = self.get_cookie(UID_COOKIE)
        SESSION_POOL.setdefault(self._session_id, set()).add(self)
        print('Connect. Cookie: %s' % self._session_id)

    def on_close(self):
        conns = SESSION_POOL[self._session_id]
        conns.remove(self)
        if conns:
            SESSION_POOL.pop(self._session_id)
        print('Disconnect. Cookie: %s' % self._session_id)

    def on_message(self, msg):
        self._mq_sock.send_json({
            'web_session_id': self._session_id,
            'data': msg})


def on_mq_recv(msgs):
    for msg in msgs:
        msg = json.loads(msg.decode())
        session_id, data = msg['web_session_id'], msg['data']
        assert session_id, 'No "session_id" in message!'

        # Временно отправка сообщений всем клиентам до тех пор,
        # # пока не будет правил привязки на основе api key
        # for _, hdls in SESSION_POOL.items():
        # for hdl in hdls:
        # hdl.write_message(data)

        # Отправка сообщения в классическом режиме:
        # Кто прислал сообщение, тот и получает ответ
        hdls = SESSION_POOL.get(session_id)
        if hdls:
            for hdl in hdls:
                hdl.write_message(data)
        else:
            print('Unknown session_id:', session_id)


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
        (r'^/$', RedirectHandler, {'url': '/index/'}),
        (r"/index/", MainHandler, {'index_path': static_path}),
        (r"/v\d+", WSHandler, {'mq': push_sock}),
        (r'/index/(.*)', StaticFileHandler, {'path': static_path}),
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
