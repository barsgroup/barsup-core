# coding: utf-8
"""Контроллеры авторизации и аутентификации."""

from yadic.container import Injectable

from barsup.auth import AVAILABLE_ACTIONS
from barsup.controller import Controller


class Authentication(Controller, metaclass=Injectable):

    """Контроллер аутентификации."""

    depends_on = ('service',)

    def login(
        self,
        login: 'str',
        password: 'str',
        web_session_id: 'str'
    ) -> r'/login':
        """
        Действие входа пользователя.

        :param login: Логин
        :param password: Пароль
        :param web_session_id: Идентификатор пользователя
        :return:
        """
        return self.service.login(
            login, password, web_session_id
        )

    def logout(
        self,
        web_session_id: 'str'
    ) -> r'/logout':
        """
        Действие выхода из системы.

        :param web_session_id: Идентификатор сессии
        :return:
        """
        pass


class PermissionController(Controller, metaclass=Injectable):

    """Контроллер для списка набора имеющихся контроллеров в системе."""

    def read(
        self,
        start: 'int'=None,
        limit: 'int'=None,
        page: 'int'=None,
        query: 'str'=None,
        filter: 'json'=None,
        group: 'str'=None,
        sort: 'json'=None
    ) -> r"/read":
        """
        Возвращает список всех контроллеров в системе.

        :return:
        """
        ctrl_set = set()
        for ctrl, action in AVAILABLE_ACTIONS:
            ctrl_set.add(ctrl)
        return map(lambda x: dict(controller=x), sorted(ctrl_set))


class PermissionAction(Controller, metaclass=Injectable):

    """Контроллер для списка действий конкретного контроллера."""

    func_filter = filter

    def read(
        self,
        filter: 'json',
        start: 'int'=None,
        limit: 'int'=None,
        page: 'int'=None,
        query: 'str'=None,
        group: 'str'=None,
        sort: 'json'=None
    ) -> r"/read":
        """
        Возвращает список действий одного контроллера.

        :param filter: Фильтр по контроллерам
        :return:
        """
        ctrl_param = filter[0]['value']
        action_set = set()
        for ctrl, action in AVAILABLE_ACTIONS:
            if ctrl == ctrl_param:
                action_set.add(action)
        return map(lambda x: dict(action=x), sorted(action_set))
