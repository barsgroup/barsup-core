# -*- coding: utf-8 -*-

import simplejson as json

import zmq
from yadic import Container as _Container

from barsup.routing import Router as _Router
from barsup.core import API as _API
from barsup import runtime as _runtime


def run(container, apps, sock_pull, sock_push, **kwargs):
    """
    Запускает worker с указанными параметрами
    """
    cont = _Container(container)
    api = _API(cont)
    # заполнение актуальной runtime-информации в соответствующем модуле
    _runtime.ACTIONS = list(api)
    _runtime.LOADED = True
    router = _Router(api.call, cont, 'controller')

    context = zmq.Context()

    pull_socket = context.socket(zmq.PULL)
    pull_socket.bind(sock_pull)
    push_socket = context.socket(zmq.PUSH)
    push_socket.bind(sock_push)

    print("ZMQ served on (%s->%s)" % (sock_pull, sock_push))

    while True:
        msg = pull_socket.recv_json()
        web_session_id = msg['web_session_id']
        data = json.loads(msg['data'])
        key = data['event']
        params = data.get('data', {})

        try:
            if not isinstance(params, dict):
                raise TypeError('Event data must be a dict!')
            status, result = router.populate(web_session_id, key, params)

        except Exception:
            status, result = False, 'Невозможно выполнить текущую операцию'
            raise
        finally:
            push_socket.send_json({
                'web_session_id': web_session_id,
                'data': json.dumps({'data': result,
                                    'success': status,
                                    'event': key},
                                   default=_serialize_to_json)})


def _serialize_to_json(obj):
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
