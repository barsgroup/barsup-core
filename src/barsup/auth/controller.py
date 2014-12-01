# coding: utf-8
from yadic.container import Injectable
from barsup.controller import DictController


class Authentication(metaclass=Injectable):
    depends_on = ('service',)

    actions = (
        (r'/login', 'login', {
            'login': 'str',
            'password': 'str',
            'web_session_id': 'str'
        }),
        (r'/logout', 'logout', {
            'web_session_id': 'str'
        }),
        (r'/is-login', 'is_login', {
            'web_session_id': 'str'
        })
    )

    def login(self, login, password, web_session_id):
        return self.service.login(
            login, password, web_session_id
        )

    def logout(self, web_session_id):
        pass

    def is_logged_in(self, web_session_id):
        return self.service.is_logged_in(web_session_id)


class Authorization(Authentication):
    def has_perm(self, uid, controller, action):
        return self.service.has_perm(uid, controller, action)


class PermissionController(metaclass=Injectable):
    depends_on = ('methods',)

    actions = (
        (r"/read", "read", {
            'start': 'int',
            'limit': 'int',
            'page': 'int',
            'filter': 'json',
            'query': 'str',
            'sort': 'json'
        }),
    )

    def read(self, *args, **kwargs):
        ctrl_set = set()
        for ctrl, action in self.methods:
            ctrl_set.add(ctrl)
        return map(lambda x: dict(controller=x), sorted(ctrl_set))


class PermissionAction(metaclass=Injectable):
    depends_on = ('methods',)

    func_filter = filter

    actions = (
        (r"/read", "read", {
            'start': 'int',
            'limit': 'int',
            'page': 'int',
            'filter': 'json',
            'query': 'str',
            'sort': 'json'
        }),
    )

    def read(self, filter, *args, **kwargs):
        ctrl_param = filter[0]['value']
        action_set = set()
        for ctrl, action in self.methods:
            if ctrl == ctrl_param:
                action_set.add(action)
        return map(lambda x: dict(action=x), sorted(action_set))