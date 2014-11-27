# coding: utf-8
from sqlalchemy.sql.elements import literal
from barsup.service import Service


class AuthenticationService(Service):

    def login(self, login, password, web_session_id):
        with self as service:
            user_id = service.session.query(
                service.db_mapper.user.id
            ).filter(
                service.db_mapper.user.login == login,
                service.db_mapper.user.password == password
            ).scalar()

        if user_id:
            with self as service:
                service.create(
                    user_id=user_id,
                    web_session_id=web_session_id)

            return True
        else:
            return False

    def logout(self, web_session_id):
        pass

    def is_logged_in(self, web_session_id):
        with self as service:
            service.filter(
                property='web_session_id',
                operator='eq',
                value=web_session_id)

            return service.session.query(
                literal(True)
            ).filter(
                service._queryset.exists()
            ).scalar()
