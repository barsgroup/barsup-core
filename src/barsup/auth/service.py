# coding: utf-8
import hashlib

from barsup.service import Service


class AuthenticationService(Service):
    def __init__(self, user_model, **kwargs):
        super().__init__(**kwargs)
        self.user_model = user_model

    def login(self, login, password, web_session_id):
        obj = self(
            self.user_model
        ).filter(
            'login', 'eq', login
        ).filter(
            'password', 'eq', password
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
        pass

    def is_logged_in(self, web_session_id):
        obj = self.filter('web_session_id', 'eq', web_session_id).get()
        return obj.get('user_id')

    def _to_md5_hash(self, value, salt='2Bq('):
        # Хеширование значения
        data = hashlib.md5((salt + value).encode())
        return data.hexdigest()


class AuthorizationService(Service):
    def __init__(self, user_role, **kwargs):
        super().__init__(**kwargs)
        self.user_role = user_role

    def has_perm(self, uid, controller, action):
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
        print (role_service.exists())
        return perm_service.exists() or role_service.exists() or False
