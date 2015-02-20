# coding:utf-8

from barsup import core


class FakeRouter:
    @staticmethod
    def register(*args):
        pass


def test_wrappable():
    """Tests the _Wrappable class behaviour"""

    class WrappableTest:
        def __init__(self):
            self.m = core._Wrappable(self.m)

        def m(self, a, b):
            return a + b

    wt = WrappableTest()
    assert wt.m(1, 2) == 3
    wt.m.wrap_with(lambda nxt, a, b: nxt(a, b * 10))
    assert wt.m(1, 2) == 21
    wt.m.wrap_with(lambda nxt, a, b: nxt(a + 1, b))
    assert wt.m(1, 2) == 22


def test_initware():
    mutable = []

    fake_container = type('Fake', (object,), {
        'itergroup': staticmethod(lambda grp: iter([]))
    })

    fend = core.Frontend(
        container=fake_container,
        api=core.API(container=fake_container, middleware=[]),
        router=FakeRouter,
        initware=[lambda *args: mutable.append(args)],
    )

    assert mutable, "Initware wasn't called!"
    assert len(mutable) == 1, "Initware was called more times than one!"

    cont_, fend_ = mutable[0]
    assert cont_ is fake_container and fend_ is fend, (
        "Initware was called with the bad arguments!"
    )


def test_api_calls():
    """Tests the API calls"""

    class FakeContainer:
        class Math:
            actions = (('GET', '/add', 'add', {}),)

            @staticmethod
            def add(a, b):
                return a + b

        class Str:
            actions = (('GET', '/upper', 'upper', {}),)

            @staticmethod
            def upper(s):
                return s.upper()

        @classmethod
        def get(cls, grp, name):
            return {
                ('controller', 'math'): cls.Math,
                ('controller', 'str'): cls.Str,
            }[(grp, name)]

        @classmethod
        def itergroup(cls, grp):
            return {
                'controller': [
                    ('math', {}, cls.Math),
                    ('str', {}, cls.Str)
                ]
            }[grp]

        def __init__(self, *args, **kwargs):
            pass

    api = core.API(container=FakeContainer, middleware=[])

    assert api.call('math', 'add', a=1, b=2) == 3
    assert api.call('str', 'upper', s='hello') == 'HELLO'

    assert list(sorted(api)) == [('math', 'add'), ('str', 'upper')]


def test_complex_example():
    """Test the complex example"""

    class Controller(object):

        actions = (('GET', '/{x:.+}/add', 'add', {}),)

        def __init__(self, y):
            self._y = y

        def add(self, x):
            return x + self._y

    class LocalContainer(core.ModuleContainer):

        def _get_entity(self, name):
            try:
                return {
                    'local.Controller': Controller
                }[name]
            except KeyError:
                return super(LocalContainer, self)._get_entity(name)

    real_api = core.init({
        'controller': {
            'cont': {
                '__realization__': 'local.Controller',
                '$y': 'bar'
            }
        },
    }, container_clz=LocalContainer, get_config=lambda x: x)

    assert real_api.populate('GET', '/cont/foo/add') == 'foobar'
