# -*- coding: utf-8 -*-
"""Набор конструкций для роутинга на контроллеры и действия."""

import re

import routes


__all__ = ('Router', 'RoutingError')


class RoutingError(Exception):

    """ Выбрасывается на уровне роутинга."""

    pass


class Router:

    """ Механизм маршрутизации по API-KEY (URL, id, etc.)."""

    PATH_VAR_RE = re.compile(r'\{(.*?)\}')

    def __init__(self):
        """Инициализирует роутер.

        :param controllers: итератор контроллеров в виде контежей (name, class)
        :type controllers: object
        """
        self._mapper = routes.Mapper()

    def register(self, method, route, controller, action):
        """Регистрирует экшн и возвращает path для его вызова

        :param method: 'GET'/'POST',...
        :type method: str
        :param route: route
        :type route: str
        :param controller: Контроллер
        :type controller: str
        :param action: Экшн
        :type action: str
        """
        route = self.PATH_VAR_RE.sub(r'{\1:.*}', route)
        self._mapper.connect(
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
