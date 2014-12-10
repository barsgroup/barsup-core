# coding: utf-8

from barsup.service import Service


class AuthenticationService(Service):
    def __init__(self, user_model, **kwargs):
        super().__init__(**kwargs)
        self.user_model = user_model

    def login(self, login, password, web_session_id):
        obj = self.service(
            self.user_model
        ).filter(
            'login', 'eq', login
        ).filter(
            'password', 'eq', password
        ).get()

        user_id = getattr(obj, 'id', None)
        if user_id:
            self.service().filter(
                'user_id', 'eq', user_id
            ).delete()

            self.service.create(
                user_id=user_id,
                web_session_id=web_session_id)

        return user_id is not None

    def logout(self, web_session_id):
        pass

    def is_logged_in(self, web_session_id):
        obj = self.filter('web_session_id', 'eq', web_session_id).get()
        return getattr(obj, 'user_id', None)


class AuthorizationService(Service):
    def __init__(self, role_model, permission_model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role_model = role_model
        self.permission_model = permission_model


    def has_perm(self, uid, controller, action):
        perm_service = self.service.filter(
            'user_id', 'eq', uid
        ).filter(
            'permission.controller', 'eq', controller
        ).filter(
            'permission.action', 'eq', action)

        role_service = self.filter(
            'user_id', 'eq', uid
        ).filter('role.is_super', 'eq', True)

        # TODO: придумать нормальный способ доставать данные в один маленький запрос
        # Объединение результатов
        # subquery = service._qs.union(role_service._qs).exists()
        # res = self.session.query(literal(True)).filter(subquery)
        # return res.scalar()

        # FIXME: пока работает некорректно, так как нет джойнов
        return perm_service.read() or role_service.read() or False