# coding:utf-8

from pytest import raises

from barsup.router import Router, RoutingError


def test_router():
    """Tests the Router"""

    router = Router()
    router.register('GET', '/{x:\d+}/{y:\d+}/sum', 'calc', 'sum')
    router.register(('GET', 'POST'), '/{n:\d+}/double', 'calc', 'double')
    router.register('*', '/echo', 'misc', 'echo')
    r = router.route

    assert r('GET', '/calc/10/20/sum') == (
        'calc', 'sum', {'x': '10', 'y': '20'})

    assert r(
        'GET', '/calc/42/double'
    ) == r(
        'POST', '/calc/42/double'
    ) == (
        'calc', 'double', {'n': '42'}
    )

    assert r(
        'GET', '/misc/echo'
    ) == r(
        'POST', '/misc/echo'
    ) == r(
        'PUT', '/misc/echo'
    ) == (
        'misc', 'echo', {}
    )

    with raises(RoutingError):
        r('GET', '/bad_route')

    with raises(RoutingError):
        r('PUT', '/calc/42/double')
