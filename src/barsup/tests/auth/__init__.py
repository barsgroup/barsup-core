# coding: utf-8
"""Вспомогательные конструкции для тестов аутентификации и авторизации."""

from barsup.tests import DBMapperMock

ADMIN_SESSION = "administrator-session-id"
USER_SESSION = "user-sessin-id"


class DBMapperAuth(DBMapperMock):

    """Заглушка для маппера."""

    def create_data(self):
        """ Создание преднастроенных данных для тестов."""
        self.create_admin()
        self.create_user()

    def create_admin(self):
        """
        Создание пользователя Foo.

        - создание пользователя "Foo"
        - создание сессии
        - создание роли "Может все"
        - привязка пользователя и роли
        """
        user = self.user(
            name="Foo",
            email="adm@test.com",
            login="administrator",
            password="secret"
        )
        session = self.web_session(
            user=user,
            web_session_id=ADMIN_SESSION
        )
        role = self.role(
            name="Может все",
            is_super=True
        )
        user_role = self.user_role(
            user=user,
            role=role
        )
        self.session.add_all([user, session, role, user_role])
        self.session.flush()

    def create_user(self):
        """
        Создание пользователя Bar.

        - создание пользователя "Bar"
        - создание сессии
        - создание роли "Может видеть пользователей"
        - привязка пользователя и роли
        """
        user = self.user(
            name="Bar",
            email="bar@test.com",
            login="bar",
            password="barbar"
        )
        session = self.web_session(
            user=user,
            web_session_id=USER_SESSION
        )
        role = self.role(
            name="Просмотр пользователей"
        )
        perm = self.permission(
            role=role,
            controller="User",
            action="read"
        )
        user_role = self.user_role(
            user=user,
            role=role
        )
        self.session.add_all([
            user, session, role, perm, user_role])
        self.session.flush()
