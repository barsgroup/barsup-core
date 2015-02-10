# -*- coding: utf-8 -*-
"""Набор конструкций для роутинга на контроллеры и действия."""

from itertools import chain

import simplejson as json
import routes


PARAM_PARSERS = {
    'json': json.loads,
    'str': str,
    'int': int,
    'list': list,
    'dict': dict
}

CATCH_ALL_PARAMS = object()


class RoutingError(Exception):
    """Выбрасывается на уровне роутинга."""

    pass


class Router:
    """Механизм маршрутизации по API-KEY (URL, id, etc.)."""

    def __init__(self, bypass_params=None):
        """.

        :param controllers: итератор контроллеров в виде контежей (name, class)
        :type controllers: object
        """
        self._mapper = routes.Mapper()
        self._param_decls = {}
        self._bypass = set(bypass_params or tuple())

    def register(self, controllers):
        """
        Register the list of pairs in form ('controller', 'acition').

        and builds the subroute for each action.
        """
        for controller, realization in controllers:
            mapper = self._mapper.submapper(
                path_prefix='/' + controller.lower())
            for action_decl in getattr(realization, 'actions'):
                route, action, params = (action_decl + (None,))[:3]
                mapper.connect(route, controller=controller, action=action)
                if params:
                    if params is CATCH_ALL_PARAMS:
                        declaration = CATCH_ALL_PARAMS
                    else:
                        try:
                            declaration = dict(
                                (k, PARAM_PARSERS[v])
                                for k, v in params.items()
                            )
                        except KeyError:
                            raise ValueError(
                                'Unknown action param type in %s!'
                                % controller
                            )
                    self._param_decls[(controller, action)] = declaration

    def route(self, key, params):
        """
        Populate the url-like API-key as action of some controller.

        :param key: API-key
        :type key: str
        :param params: action params
        :type params: dict
        """
        dest = self._mapper.match(key)
        if not dest:
            raise RoutingError('Wrong key: "%s"!' % key)

        controller_name, action_name = map(dest.pop, ('controller', 'action'))

        parsers = self._param_decls.get((controller_name, action_name), {})
        if parsers is CATCH_ALL_PARAMS:
            parsed_params = params.copy()
            parsed_params.update(dest)
        else:
            parsed_params = {}
            for name, value in chain(dest.items(), params.items()):
                if name == 'format':
                    continue
                elif name in self._bypass:
                    parsed_params[name] = value
                    continue
                try:
                    parser = parsers[name]
                except KeyError:
                    if name in dest:
                        # параметры из url могут быть и не задекларированы,
                        # тогда они передаются "как есть"
                        def parser(x):
                            return x
                    else:
                        # тогда как прочие должны декларироваться
                        raise RoutingError(
                            'Undeclared parameter "%s" (%s.%s)'
                            % (name, controller_name, action_name)
                        )
                try:
                    parsed_params[name] = parser(value)
                except (TypeError, ValueError):
                    raise RoutingError(
                        'Wrong value for param "%s" (%s.%s)'
                        % (name, controller_name, action_name)
                    )

        return controller_name, action_name, parsed_params


__all__ = ('Router',)
