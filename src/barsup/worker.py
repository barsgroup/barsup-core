# -*- coding: utf-8 -*-

import simplejson as json

import zmq

from barsup.container import Container as _Container
from barsup.routing import Router as _Router
from barsup.core import API as _API


def run(container, apps, sock_pull, sock_push, **kwargs):
    """
    Запускает worker с указанными параметрами
    """
    cont = _Container(container)
    router = _Router(_API(cont).call, cont, 'controller')

    context = zmq.Context()

    pull_socket = context.socket(zmq.PULL)
    pull_socket.bind(sock_pull)
    push_socket = context.socket(zmq.PUSH)
    push_socket.bind(sock_push)

    print("ZMQ served on (%s->%s)" % (sock_pull, sock_push))

    while True:
        msg = pull_socket.recv_json()
        uid = msg['uid']
        data = json.loads(msg['data'])
        key = data['event']
        params = data.get('data', {})

        try:
            if not isinstance(params, dict):
                raise TypeError('Event data must be a dict!')
            result = router.populate(uid, key, params)
            answer = json.dumps(
                {'event': key, 'data': result},
                default=_default_dump
            )
        except Exception:
            answer = json.dumps({
                'event': key,
                'error': 'Невозможно выполнить текущую операцию'})
            raise
        finally:
            push_socket.send_json({
                'uid': uid,
                'data': answer
            })


def _default_dump(obj):
    if isinstance(obj, map):
        return [o for o in obj]
    else:
        raise TypeError('Type "{0}" not supported'.format(obj))

DEFAULT_PARAMS = {
    'container': {},
    'apps': [],
    'sock_pull': 'tcp://*:3002',
    'sock_push': 'tcp://*:3001',
}
