# coding: utf-8
"""Конструкции для работы с API."""

from functools import partial
from collections import namedtuple
import re
import inspect

from yadic.container import Container as _Container
from yadic.util import deep_merge as _deep_merge

from barsup.util import load_configs as _load_configs
from barsup import validators as _validators


CATCH_ALL_PARAMS = object()

Redirection = namedtuple('Redirection', 'module path context')


class _Wrappable:

    """Оборачиватель метода/функции в слои middleware."""

    def __init__(self, fn):
        """.

        :param fn: Функция для оборачивания
        """
        self.fn = fn

    def wrap_with(self, mware):
        """
        Оборачивает функцию в mware.

        :param mware: MW
        """
        self.fn = partial(mware, self.fn)

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)


class ModuleContainer(_Container):

    """Реализация контейнера для использования на уровне модулей."""

    _PATH_RE = re.compile(r'(?:(.*)/)?([^/]+)')

    def __init__(self, config, parent):
        """.

        :param config:
        :param parent:
        """
        self._parent = parent
        super().__init__(config)

    def get(self, group, name):
        """См. базовую документацию."""
        if (group, name) == ('__internal__', '__this__'):
            return self
        path, real_name = self._PATH_RE.match(name).groups()
        if path is None:
            ctr = super()
        else:
            ctr = self
            for step in path.split('/'):
                if step == '..':
                    ctr = ctr._parent
                elif step == '':
                    raise ValueError('Unobtainable path: $r!' % path)
                else:
                    ctr = ctr.get('module', step)._container
        return ctr.get(group, real_name)


class API:
    """
    Обёртка над слоем контроллеров.

    Добавляет уровень middleware и отвечает за непосредственное общение с
    контроллерами.
    """

    CONTROLLER_GROUP = 'controller'

    def __init__(self, *, container, middleware):
        """Инициализирует API.

        :param container: DI-контейнер
        :type container: object
        :param middleware: iterable, задающее посл-ть middleware
        :type middleware: list
        :param controller_group: ключ-наименование группы контроллеров
        :type controller_group: str
        """
        def initialize(nxt, *args, **kwargs):
            """initialize.

            Middleware, создающая для "потомков" пустой контекст
            (если он ещё не создан)
            """
            kwargs.setdefault('_context', {})
            return nxt(*args, **kwargs)

        def finalize(nxt, controller, action, *args, **kwargs):
            """finalize.

            Middleware, убирающая контекст из параметров перед вызовом
            конечного экшна. Если вызываемый экшн - не конечный,
            то текущий экшн добавляется в список, хранящий
            маршрут роутинга
            """
            if 'subroute' not in kwargs:
                kwargs.pop('_context', None)
            else:
                kwargs['_context'].setdefault('path', []).append(
                    (controller, action))
            return nxt(controller, action, *args, **kwargs)

        # оборачиывание метода, вызывающего экшны, в middleware
        call = self.call = _Wrappable(self.call)
        call.wrap_with(finalize)
        for mw in middleware[::-1]:
            call.wrap_with(mw)
        call.wrap_with(initialize)

        self._container = container

    def call(self, controller, action, **kwargs):
        """
        Вызывает API-функцию с указанными параметрами.

        Функция ищется по паре "контроллер" + "экшн"
        """
        ctl = self._container.get(self.CONTROLLER_GROUP, controller)
        try:
            action = getattr(ctl, action)
        except AttributeError:
            raise ValueError(
                "The \"%s\" controller don't have an action \"%s\"!"
                % (controller, action))
        return action(**kwargs)

    def __iter__(self):
        """Возвращает итератор пар вида (controller, action)."""
        for (controller, _, realization) in self._container.itergroup(
            self.CONTROLLER_GROUP
        ):
            for attr, val in realization.__dict__.items():
                if not attr.startswith('_') and (
                    callable(val) or inspect.ismethoddescriptor(val)
                ):
                    yield (controller, attr)


class Frontend:
    """Frontend, используемый для взаимодействия с системой"""

    def __init__(self, *, spec, container, api, router, initware):
        """Инициализирует Frontend.

        :param spec: словарь со swagger specifiation
        :type spec: dict
        :param container: DI Container
        :type container: ModuleContainer
        :param api: API
        :type api: API
        :param router: Router
        :type router: barsup.router.Router
        :param initware: iterable, задающее посл-ть initware
        :type initware: list
        """
        self.api = api
        self._container = container
        self._router = router

        self._action_specs = {}
        for route, methods in spec.get('paths', {}).items():
            for method, mspec in methods.items():
                try:
                    controller, action = mspec['operationId'].split('.')
                except (KeyError, ValueError):
                    raise RuntimeError(
                        'Wrong <operationId> format! (%r at %r:%r)'
                        % (mspec.get('operationId'), route, method)
                    )
                else:
                    self._router.register(
                        method.upper(),
                        route,
                        controller,
                        action
                    )
                    self._action_specs[(controller, action)] = (
                        mspec.get('parameters', []),
                        mspec.get('responses', []),
                    )

        # вызов возможных инициализаторов
        for iw in initware:
            iw(container, self)

    def populate(self, method, path, **params):
        """Обрабатывает вызов экшна.

        :param method: 'GET'/'POST'/...
        :type method: str
        :param path: routing path
        :type path: str
        """
        controller, action, path_params = self._router.route(method, path)
        # описание обязано быть, ибо по нему строился роутинг,
        # поэтому не ловится KeyError
        (param_spec, resp_spec) = self._action_specs[(controller, action)]
        out_params = {}
        query_params = params.copy()
        for param in param_spec:
            try:
                validate = _validators.VALIDATORS[param['type']](**param)
            except KeyError:
                raise _validators.ValidationError(
                    'Unknown parameter type: %r' % param.get('type')
                )
            else:
                # TODO: дореализовать обработку параметров
                # в теле запроса и проч
                assert param['in'] in {'path', 'query'}
                # валидатор перемещает параметр из одного из
                # входных словарей в выходной словарь параметров
                validate(
                    in_dict=(
                        path_params if param['in'] == 'path'
                        else query_params
                    ),
                    out_dict=out_params
                )
        # сохранение контекста
        if '_context' in query_params:
            out_params['_context'] = query_params.pop('_context')
        try:
            result = self.api.call(controller, action, **out_params)
        except Exception as e:
            # TODO: сделать проверку на допустимость исключения
            # (наличие соответствующего статус-кода в responses)
            raise
        if isinstance(result, Redirection):
            result = result.module.populate(
                method,
                result.path,
                _context=result.context,
                **query_params
            )
        return result


def get_defaults():
    """Возвращает конфигурацию по умолчанию"""
    return {
        'controller': {},
        'frontend': {
            'default': {
                '__realization__': 'barsup.core.Frontend',
                '__type__': 'singleton',
                'container:__internal__': '__this__',
                'api': 'default',
                'router': 'default',
                'initware': []
            },
        },
        'api': {
            'default': {
                '__realization__': 'barsup.core.API',
                '__type__': 'singleton',
                'container:__internal__': '__this__',
                'middleware': []
            },
        },
        'router': {
            'default': {
                '__realization__': 'barsup.router.Router',
                '__type__': 'singleton'
            }
        },
        'module': {
            '__default__': {
                '__realization__': 'barsup.core.init',
                '__type__': 'singleton',
                'parent:__internal__': '__this__'
            }
        }
    }


def init(
    config,
    *,
    container_clz=ModuleContainer,
    get_config=_load_configs,
    get_defaults=get_defaults,
    parent=None
):
    """
    Производит инициализацию ядра.

    Согласно указанной конфигурации и возвращает экземпляр API
    :param get_config: callable, возвращающий конфигурацию в виде словаря
    :type get_config: object
    :param container_clz: class реализации DI-контейнера
    :type container_clz: object
    :param get_defaults: callable, возвращающий умолчательную конфигурацию
    :type get_defaults: object
    :return type: Frontend
    """
    cont = container_clz(
        config=_deep_merge(
            get_defaults(),
            get_config(config),
            fn=lambda x, y, m, p: y),
        parent=parent
    )
    return cont.get('frontend', 'default')


def iter_frontends(f):
    """
    Возвращает итератор пар, для дочерних модулей указанного Frontend.

    Формат итератора: (кортеж-путь_до_Frontend, экземпляр Frontend)
    """
    yield tuple(), f
    cont = f._container
    for item in cont.itergroup('module'):
        module = item[0]
        for path, inst in iter_frontends(cont.get('module', module)):
            yield (module,) + path, inst


__all__ = ('init', 'API', 'ModuleContainer')
