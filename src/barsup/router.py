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

    def register(self, controllers):
        """Регистрирует контроллеры.

        :param controllers: список пак вида ('ctl_name', ctl_realization)
        :type controllers: list
        """
        for controller, realization in controllers:
            mapper = self._mapper.submapper(
                path_prefix='/' + controller.lower())
            for action_decl in getattr(realization, 'actions'):
                route, action, _ = (action_decl + (None,))[:3]
                mapper.connect(route, controller=controller, action=action)

    def route(self, method, path):
        """Возвращает контроллер, экшн и параметры по url(path).

        :param method: 'GET'/'POST'/...
        :type key: str
        :param path: routing path
        :type path: str
        """
        dest = self._mapper.match(path)
        if not dest:
            raise RoutingError('Wrong path: "%s"!' % path)

        controller_name, action_name = map(dest.pop, ('controller', 'action'))
        return controller_name, action_name, dest


__all__ = ('Router',)
