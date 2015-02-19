# coding:utf-8

from pytest import raises

from barsup.router import Router, RoutingError


def test_router():
    """Tests the Router"""

    class CalcController:
        actions = (
            ('/{x:\d+}/{y:\d+}/sum', 'sum'),
            ('/{n:\d+}/double', 'double'),
        )

    router = Router()
    router.register((
        ('calc', CalcController),
    ))
    r = router.route

    assert r('GET', '/calc/10/20/sum') == (
        'calc', 'sum', {'x': '10', 'y': '20'})
    assert r('GET', '/calc/42/double') == (
        'calc', 'double', {'n': '42'})

    with raises(RoutingError):
        r('GET', '/bad_route')
