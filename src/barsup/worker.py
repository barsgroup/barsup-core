# -*- coding: utf-8 -*-

import json

import zmq

from container import Container as _Container
from routing import Router as _Router


def _dmp(x):
    print x, type(x)
    return None


def run(container, apps, sock_pull, sock_push):
    """ч>
    Запускает worker с указанными параметрами\
    """
    cont = _Container(container)
    router = _Router(cont, 'controller')

    context = zmq.Context()

    pull_socket = context.socket(zmq.PULL)
    pull_socket.bind(sock_pull)
    push_socket = context.socket(zmq.PUSH)
    push_socket.bind(sock_push)

    print ("ZMQ served on (%s->%s)" % (sock_pull, sock_push))
    while True:
        msg = pull_socket.recv_json()
        uid = msg['uid']
        data = json.loads(msg['data'])
        key = data['event']
        params = data.get('data', {})
        msg = {
            'uid': uid,
            'data': json.dumps({
                'event': key,
                'data': router.populate(uid, key, params)
            }, default=_dmp)
        }
        push_socket.send_json(msg)


DEFAULT_PARAMS = {
    'container': {},
    'apps': [],
    'sock_pull': 'tcp://*:3002',
    'sock_push': 'tcp://*:3001',
}
