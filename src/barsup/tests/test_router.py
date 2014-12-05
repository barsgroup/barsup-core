# coding:utf-8

from pytest import raises
from barsup.router import Router


def test_router():
    """Tests the Router"""

    class CalcController:

        actions = (
            ('/{x:\d+}/{y:\d+}/sum', 'sum'),
            ('/{x:\d+}/{y:\d+}/mul', 'mul'),
            ('/{x:\d+}/double', 'double'),
        )

    class Parametrized:

        actions = (
            ('/{x:\d+}/add', 'add',
             {'x': 'int', 'y': 'int', 'msg': 'str', 'raw': 'json'}),
        )

    router = Router(
        controllers=(
            ('calc', CalcController),
            ('par', Parametrized),
        ),
        bypass_params=set(('bypass',))
    )
    r = router.route

    assert r('/calc/10/20/sum', {}) == ('calc', 'sum', {'x': '10', 'y': '20'})
    assert r('/calc/42/double', {'bypass': 101}) == (
        'calc', 'double', {'x': '42', 'bypass': 101})

    assert r('/par/10/add', {'y': '20', 'msg': 'Hi!'}) == (
        'par', 'add', {'x': 10, 'y': 20, 'msg': 'Hi!'})

    with raises(ValueError):
        r('/parametrized/1000/add', {'z': 1})

    with raises(ValueError):
        r('/parametrized/1000/add', {'y': 'asd'})

    with raises(ValueError):
        r('/parametrized/1000/add', {'raw': '!'})