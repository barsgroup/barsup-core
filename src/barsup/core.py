# coding: utf-8

from functools import partial

from yadic.container import Container as _Container
from yadic.util import deep_merge as _deep_merge


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
                 container, middleware, initware, router,
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
        call = self.call = _Wrappable(self._call)
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

        # вызов возможных инициализаторов
        for iw in initware:
            iw(container, self)

    def _call(self, controller, action, **kwargs):
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
         defaults=lambda: {
             'api_options': {
                 'default': {
                     '__realization__': 'builtins.dict',
                     'middleware': [],
                     'initware': [],
                     'router:api_options': 'router',
                 },
                 'api_class': {
                     '__realization__': 'barsup.core.API',
                     '__type__': 'static'
                 },
                 'router': {
                     '__realization__': 'barsup.router.Router',
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
        _deep_merge(defaults(), config, fn=lambda x, y, m, p: y))
    api = cont.get('api_options', 'api_class')(
        container=cont,
        **cont.get('api_options', 'default'))
    return api


__all__ = (init,)
