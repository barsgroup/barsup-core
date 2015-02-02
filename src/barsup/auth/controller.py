# coding: utf-8
"""
Контроллеры авторизации и аутентификации
"""

from yadic.container import Injectable

from barsup.auth import AVAILABLE_ACTIONS
from barsup.controller import Controller


class Authentication(Controller, metaclass=Injectable):
    """
    Контроллер аутентификации
    """
    depends_on = ('service',)

    def login(
        self,
        login: 'str',
        password: 'str',
        web_session_id: 'str'
    ) -> r'/login':
        return self.service.login(
            login, password, web_session_id
        )

    def logout(
        self,
        web_session_id: 'str'
    ) -> r'/logout':
        pass


class PermissionController(Controller, metaclass=Injectable):
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
        ctrl_set = set()
        for ctrl, action in AVAILABLE_ACTIONS:
            ctrl_set.add(ctrl)
        return map(lambda x: dict(controller=x), sorted(ctrl_set))


class PermissionAction(Controller, metaclass=Injectable):
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
        ctrl_param = filter[0]['value']
        action_set = set()
        for ctrl, action in AVAILABLE_ACTIONS:
            if ctrl == ctrl_param:
                action_set.add(action)
        return map(lambda x: dict(action=x), sorted(action_set))
