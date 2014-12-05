# coding:utf-8

from yadic.container import Container

from barsup.core import _Wrappable, API, init


def test_wrappable():
    """Tests the _Wrappable class behaviour"""

    class WrappableTest:
        def __init__(self):
            self.m = _Wrappable(self.m)

        def m(self, a, b):
            return a + b

    wt = WrappableTest()
    assert wt.m(1, 2) == 3
    wt.m.wrap_with(lambda nxt, a, b: nxt(a, b * 10))
    assert wt.m(1, 2) == 21
    wt.m.wrap_with(lambda nxt, a, b: nxt(a + 1, b))
    assert wt.m(1, 2) == 22


def test_api():
    """Tests the API"""

    class FakeContainer:

        class Math:

            actions = (('/add', 'add', {}),)

            @staticmethod
            def add(a, b):
                return a + b

        class Str:

            actions = (('/upper', 'upper', {}),)

            @staticmethod
            def upper(s):
                return s.upper()

        class Router(object):

            def __init__(self, controllers):
                pass

            @staticmethod
            def route(key, params):
                controller, action = key.split('/')[1:3]
                return controller, action, params

        @staticmethod
        def args_to_strs(nxt, *args, **kwargs):
            args = map(str, args)
            kwargs = {k: str(v) for (k, v) in kwargs.items()}
            return nxt(*args, **kwargs)

        @staticmethod
        def res_to_str(nxt, *args, **kwargs):
            return str(nxt(*args, **kwargs))

        @classmethod
        def get(cls, grp, name):
            return {
                ('controller', 'math'): cls.Math,
                ('controller', 'str'): cls.Str,
                ('middleware', 'res_to_str'): cls.res_to_str,
                ('middleware', 'args_to_strs'): cls.args_to_strs,
                ('api_options', 'api_class'): API,
                ('api_options', 'default'): {
                    'middleware': [cls.res_to_str,
                                   cls.args_to_strs],
                    'router': cls.Router
                }
            }[(grp, name)]

        @classmethod
        def itergroup(cls, grp):
            return {
                'controller': [
                    ('math', {}, cls.Math),
                    ('str', {}, cls.Str)
                ]
            }[grp]

        def __init__(self, *args):
            pass

    api = init({}, container_clz=FakeContainer)

    assert api.call('math', 'add', a=1, b=2) == '12'
    assert api.call('str', 'upper', s='hello') == 'HELLO'

    assert list(sorted(api)) == [('math', 'add'), ('str', 'upper')]


def test_complex_example():
    """Test the complex example"""
    class Controller(object):

        actions = (('/{x:\d+}/add', 'add', {'x': 'int'}),)

        def __init__(self, y):
            self._y = y

        def add(self, x):
            return x + self._y

    class LocalContainer(Container):

        def _get_entity(self, name):
            try:
                return {
                    'local.Controller': Controller
                }[name]
            except KeyError:
                return super(LocalContainer, self)._get_entity(name)

    real_api = init({
        'controller': {
            'cont': {
                '__realization__': 'local.Controller',
                '$y': 100
            }
        },
    }, container_clz=LocalContainer)

    assert real_api.populate('/cont/10/add') == 110
