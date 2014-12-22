# -*- coding: utf-8 -*-

import simplejson as json
import zmq

from barsup import core
from barsup.util import serialize_to_json


def run(container, apps, sock_pull, sock_push, **kwargs):
    """
    Запускает worker с указанными параметрами
    """
    api = core.init(container)
    # заполнение актуальной runtime-информации в соответствующем модуле

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
            status, result = api.populate(
                key, web_session_id=web_session_id, **params)

        except Exception:
            status, result = False, 'Невозможно выполнить текущую операцию'
            raise
        finally:
            push_socket.send_json({
                'web_session_id': web_session_id,
                'data': json.dumps({'data': result,
                                    'success': status,
                                    'event': key},
                                   default=serialize_to_json)})


DEFAULT_PARAMS = {
    'container': {},
    'apps': [],
    'sock_pull': 'tcp://*:3002',
    'sock_push': 'tcp://*:3001',
}
