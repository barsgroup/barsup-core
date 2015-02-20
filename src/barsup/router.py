# -*- coding: utf-8 -*-
"""Набор конструкций для роутинга на контроллеры и действия."""

import routes


class RoutingError(Exception):
    """Выбрасывается на уровне роутинга."""

    pass


class Router:
    """Механизм маршрутизации по API-KEY (URL, id, etc.)."""

    def __init__(self):
        """Инициализирует роутер.

        :param controllers: итератор контроллеров в виде контежей (name, class)
        :type controllers: object
        """
        self._mapper = routes.Mapper()
        self._submappers = {}

    def register(self, method, route, controller, action):
        """Регистрирует

        :param method: 'GET'/'POST',...
        :type method: str
        :param route: route
        :type route: str
        :param controller: Контроллер
        :type controller: str
        :param action: Экшн
        :type action: str
        """
        mapper = self._submappers.get(controller)
        if not mapper:
            mapper = self._mapper.submapper(
                path_prefix='/' + controller.lower()
            )
        mapper.connect(
            route, controller=controller, action=action,
            conditions={} if method == '*' else {
                'method': [method] if isinstance(method, str) else method
            }
        )

    def route(self, method, path):
        """Возвращает контроллер, экшн и параметры по url(path).

        :param method: 'GET" или ('GET', 'POST'...)
        :type key: object
        :param path: routing path
        :type path: str
        """
        dest = self._mapper.match(path, environ={'REQUEST_METHOD': method})
        if not dest:
            raise RoutingError('Wrong path: "%s"!' % path)

        controller_name, action_name = map(dest.pop, ('controller', 'action'))
        return controller_name, action_name, dest


__all__ = ('Router',)
