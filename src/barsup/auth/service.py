# coding: utf-8
"""Сервисы для аутентфикации и авторизации."""
from barsup.auth.util import to_md5_hash

from barsup.service import Service


class AuthenticationService(Service):
    """Сервис аутентификации."""

    METHODS = {
        None: lambda x: x,
        'md5': to_md5_hash
    }

    def __init__(self, user_model, hash=None, **kwargs):
        """.

        :param user_model: Ссылка на модель пользователей
        :param dict kwargs: Доп. необходимые параметры
        :return:
        """
        super().__init__(**kwargs)
        self.method = self.METHODS[hash]
        self.user_model = user_model

    def login(self, login, password, web_session_id):
        """
        Процедура входа в систему.

        :param str login: Логин
        :param str password: Пароль
        :param str web_session_id: Идентификатор сессии
        :return bool: Удалось ли залогиниться
        """
        obj = self(
            self.user_model
        ).filter(
            'login', 'eq', login
        ).filter(
            'password', 'eq', self.method(password)
        ).get()

        user_id = obj.get('id')
        if user_id:
            self.filter(
                'user_id', 'eq', user_id
            ).delete()

            self.create(
                user_id=user_id,
                web_session_id=web_session_id)

        return user_id is not None

    def logout(self, web_session_id):
        """
        Процедура выхода из системы.

        :param str web_session_id: Идентификатор сессии
        :return bool: Удалось ли разлогиниться
        """
        pass

    def is_logged_in(self, web_session_id):
        """
        Процедура проверки, залогинен ли пользователь.

        :param str web_session_id:  Идентификатор сессии
        :return int: Идентификатор пользователя
        """
        obj = self.filter('web_session_id', 'eq', web_session_id).get()
        return obj.get('user_id')


class AuthorizationService(Service):
    """Сервис авторизации."""

    def __init__(self, user_role, **kwargs):
        """.

        :param user_role: Ссылка на модель пользователей
        :param dict kwargs: Доп. необходимые параметры
        :return:
        """
        super().__init__(**kwargs)
        self.user_role = user_role

    def has_perm(self, uid, controller, action):
        """
        Проверка прав на действие.

        :param int uid: Идентификатор пользователя
        :param str controller: Контроллер
        :param str action: Действие
        :return bool: Есть ли право выполнения
        """
        perm_service = self.filter(
            'user_id', 'eq', uid
        ).filter(
            'permission.controller', 'eq', controller
        ).filter(
            'permission.action', 'eq', action)

        role_service = self(self.user_role).filter(
            'user_id', 'eq', uid
        ).filter('role.is_super', 'eq', True)

        # TODO: придумать нормальный способ
        # получения данных в один маленький запрос
        # Объединение результатов
        # subquery = service._qs.union(role_service._qs).exists()
        # res = self.session.query(literal(True)).filter(subquery)
        # return res.scalar()
        return perm_service.exists() or role_service.exists() or False
