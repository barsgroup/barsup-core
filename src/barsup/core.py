# coding: utf-8

from functools import partial


class _Wrappable(object):
    """
    Оборачиватель метода/функции в слои middleware
    """
    def __init__(self, fn):
        self.fn = fn

    def wrap_with(self, mware):
        self.fn = partial(mware, self.fn)

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)


class API(object):
    """
    Обёртка над слоем контроллеров, добавляющая уровень middleware
    и отвечающая за непосредственное общение с контроллерами.
    """
    default_options = {
        'middleware': [],
    }

    def __init__(self, container,
                 option_group='api_options',
                 middleware_group='middleware',
                 controller_group='controller'):
        """
        :param container: DI-контейнер
        :type container: object
        :param option_group: ключ-наименование группы опций
        :type option_group: str
        :param middleware_group: ключ-наименование группы middleware
        :type middleware_group: str
        :param controller_group: ключ-наименование группы контроллеров
        :type controller_group: str
        """
        init_errors = []

        def err(e):
            init_errors.append('API init error: %s' % e)

        # options
        options = self.default_options.copy()
        try:
            opt_list = container.itergroup(option_group)
        except (ValueError, KeyError):
            pass
        else:
            for option_name, _, option_value in opt_list:
                if option_name not in self.default_options:
                    err('Wrong option name "%s"!' % option_name)
                else:
                    options[option_name] = option_value

        # middlewares
        middleware = []
        for mw in options['middleware']:
            try:
                middleware.append(container.get(middleware_group, mw))
            except (ValueError, TypeError) as e:
                err(e)

        call = self.call = _Wrappable(self.call)
        for mw in middleware[::-1]:
            call.wrap_with(mw)

        # controllers
        try:
            for _ in container.itergroup(controller_group):
                break
            else:
                raise ValueError('No one controller was configured!')
        except (ValueError, TypeError) as e:
            err(e)
        else:
            self._controller_group = controller_group

        if init_errors:
            raise RuntimeError(
                '\n'.join(init_errors) +
                '\nAPI was''n properly configured!')

        self._container = container

    def call(self, controller, action, **kwargs):
        """
        Вызов API-функции с указанными параметрами.
        Функция ищется по паре "контроллер" + "экшн"
        """
        ctl = self._container.get(self._controller_group, controller)
        action = getattr(ctl, action)
        return action(**kwargs)


__all__ = (API,)


if __name__ == '__main__':

    class WrappableTest(object):
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
    class FakeContainer(object):

        class Math(object):

            @staticmethod
            def add(a, b):
                return a + b

        class Str(object):

            @staticmethod
            def upper(s):
                return s.upper()

        @staticmethod
        def log(nxt, controller, action, **kwargs):
            print("Calling %s:%s(%s)..." % (controller, action,
                                            ','.join('%s=%r' % p
                                                     for p in kwargs.items()))),
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
            }[(grp, name)]

        @staticmethod
        def itergroup(grp):
            return {
                'api_options': [
                    ('middleware', None, ['log',
                                          'res_to_str',
                                          'args_to_strs'])],
                'controller': [None]
            }[grp]

    api = API(FakeContainer)

    assert api.call('math', 'add', a=1, b=2) == '12'
    assert api.call('str', 'upper', s='hello') == 'HELLO'
