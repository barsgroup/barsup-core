# coding: utf-8
from yadic.container import Injectable


class Authentication(metaclass=Injectable):
    depends_on = ('service',)

    def login(self,
              login: 'str',
              password: 'str',
              web_session_id: 'str') -> r'/login':
        return self.service.login(
            login, password, web_session_id
        )

    def logout(self,
               web_session_id: 'str') -> r'/logout':
        pass

    def is_logged_in(self,
                     web_session_id: 'str') -> r'/is-login':
        return self.service.is_logged_in(web_session_id)


class Authorization(metaclass=Injectable):
    depends_on = ('service',)

    def has_perm(self, uid, controller, action):
        return self.service.has_perm(uid, controller, action)


class PermissionController(metaclass=Injectable):
    depends_on = ('methods',)

    def read(self,
             start: 'int'=None,
             limit: 'int'=None,
             page: 'int'=None,
             query: 'str'=None,
             filter: 'json'=None,
             group: 'str'=None,
             sort: 'json'=None) -> r"/read":
        ctrl_set = set()
        for ctrl, action in self.methods:
            ctrl_set.add(ctrl)
        return map(lambda x: dict(controller=x), sorted(ctrl_set))


class PermissionAction(metaclass=Injectable):
    depends_on = ('methods',)

    func_filter = filter

    def read(self,
             filter: 'json',
             start: 'int'=None,
             limit: 'int'=None,
             page: 'int'=None,
             query: 'str'=None,
             group: 'str'=None,
             sort: 'json'=None) -> r"/read":

        ctrl_param = filter[0]['value']
        action_set = set()
        for ctrl, action in self.methods:
            if ctrl == ctrl_param:
                action_set.add(action)
        return map(lambda x: dict(action=x), sorted(action_set))