# -*- coding: utf-8 -*-

import json

import zmq

from sys import stderr

from container import Container as _Container
from routing import Router as _Router


def run(container, apps, sock_pull, sock_push, **kwargs):
    """
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

        try:
            if not isinstance(params, dict):
                raise TypeError('Event data must be a dict!')
            result = router.populate(uid, key, params)
            answer = json.dumps({'event': key, 'data': result})
        except (ValueError, TypeError) as e:
            stderr.write(
                'Error: "%s" (%s, %r)\n' % (e, key, params)
            )
            answer = json.dumps({'event': key, 'error': unicode(e)})
        except:
            answer = json.dumps({
                'event': key,
                'error': u'Невозможно выполнить текущую операцию'})
            push_socket.send_json({
                'uid': uid,
                'data': answer
            })
            raise

        push_socket.send_json({'uid': uid, 'data': answer})


DEFAULT_PARAMS = {
    'container': {},
    'apps': [],
    'sock_pull': 'tcp://*:3002',
    'sock_push': 'tcp://*:3001',
}
