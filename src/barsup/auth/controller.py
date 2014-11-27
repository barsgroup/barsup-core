# coding: utf-8
from barsup.container import Injectable


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

    def is_login(self, web_session_id):
        return self.service.is_login(web_session_id)