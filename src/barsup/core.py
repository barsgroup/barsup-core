# coding: utf-8

from functools import partial

from yadic.container import Container as _Container
from yadic.util import deep_merge as _deep_merge

from barsup.routing import Router as _Router
from barsup import runtime as _runtime


class _Wrappable:
    """
    Оборачиватель метода/функции в слои middleware
    """
    def __init__(self, fn):
        self.fn = fn

    def wrap_with(self, mware):
        self.fn = partial(mware, self.fn)

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)


class API:
    """
    Обёртка над слоем контроллеров, добавляющая уровень middleware
    и отвечающая за непосредственное общение с контроллерами.
    """

    def __init__(self, *,
                 container, middleware, router,
                 controller_group='controller'):
        """
        :param container: DI-контейнер
        :type container: object
        :param middleware: iterable, задающее посл-ть middleware
        :type middleware: list
        :param router: class роутера
        :type container: type
        :param controller_group: ключ-наименование группы контроллеров
        :type controller_group: str
        """
        # завертывание в middleware
        call = self.call = _Wrappable(self.call)
        for mw in middleware[::-1]:
            call.wrap_with(mw)

        # Контроллер должен быть хотя бы один!
        for _ in container.itergroup(controller_group):
            break
        else:
            raise ValueError('No one controller was configured!')

        self._controller_group = controller_group
        self._container = container

        self._router = router(controllers=(
            (name, clz) for (name, _, clz) in
            container.itergroup(controller_group)
        ))

    def call(self, controller, action, **kwargs):
        """Вызывает API-функцию с указанными параметрами.
        Функция ищется по паре "контроллер" + "экшн"
        """
        ctl = self._container.get(self._controller_group, controller)
        try:
            action = getattr(ctl, action)
        except AttributeError:
            raise ValueError(
                "The \"%s\" controller don't have an action \"%s\"!"
                % (controller, action))
        return action(**kwargs)

    def __iter__(self):
        """Возвращает итератор пар вида (controller, action)"""
        for (controller, _, realization) in self._container.itergroup(
            self._controller_group
        ):
            for action_decl in getattr(realization, 'actions', ()):
                yield (controller, action_decl[1])

    def populate(self, key, **kwargs):
        """Вызывает API-функцию по ключу.
        параметры передаются в вызываемую функцию"""
        ctl, action, params = self._router.route(key, kwargs)
        return self.call(ctl, action, **params)


def init(config, *,
         container_clz=_Container,
         defaults={
             'api_options': {
                 'default': {
                     '__realization__': 'builtins.dict',
                     'middleware:middleware': [],
                     'router:api_options': 'router',
                 },
                 'api_class': {
                     '__realization__': 'barsup.core.API',
                     '__type__': 'static'
                 },
                 'router': {
                     '__realization__': 'barsup.routing.Router',
                     '__type__': 'static'
                 }
             }
         }):
    """Производит инициализацию ядра согласно
    указанной конфигурации и возвращает экземпляр API
    :param config: конфигурация
    :type config: dict
    :return type: API"""
    cont = container_clz(
        _deep_merge(defaults.copy(), config,
                    fn=lambda x, y, m, p: y))
    api = cont.get('api_options', 'api_class')(
        container=cont,
        **cont.get('api_options', 'default'))
    _runtime.ACTIONS = tuple(api)
    _runtime.LOADED = True
    return api


__all__ = (init,)


if __name__ == '__main__':

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

    # API test
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
        def log(nxt, controller, action, **kwargs):
            print("Calling %s:%s(%s)..." % (
                controller, action,
                ','.join('%s=%r' % p for p in kwargs.items())
            ), end='')
            res = nxt(controller, action, **kwargs)
            print("returns %r" % res)
            return res

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
                ('middleware', 'log'): cls.log,
                ('api_options', 'api_class'): API,
                ('api_options', 'default'): {
                    'middleware': [cls.log,
                                   cls.res_to_str,
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

    # интеграционный тест с yadic-контейнером и штатным роутером

    class Controller(object):

        actions = (('/{x:\d+}/add', 'add', {'x': 'int'}),)

        def __init__(self, y):
            self._y = y

        def add(self, x):
            return x + self._y

    class LocalContainer(_Container):

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
