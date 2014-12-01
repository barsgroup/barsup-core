# coding: utf-8
from yadic.container import Injectable
from barsup.service import Service


class AuthenticationService(Service):
    depends_on = Service.depends_on + (
        'user_model', "web_session_model"
    )

    def __init__(self, user_model, web_session_model, model=None, **kwargs):
        self.user_model = user_model
        self.web_session_model = web_session_model
        super(AuthenticationService, self).__init__(model=model, **kwargs)

    def login(self, login, password, web_session_id):
        service = self.create_service(self.user_model)
        service.filter('login', 'eq', login)
        service.filter('password', 'eq', password)

        user_id = getattr(service.read(), 'id', None)
        if user_id:
            service = self.create_service(self.web_session_model)
            service.filter('user_id', 'eq', user_id)
            service.delete()

            service = self.create_service(self.web_session_model)
            service.create(
                user_id=user_id,
                web_session_id=web_session_id)

        return user_id is not None

    def logout(self, web_session_id):
        pass

    def is_logged_in(self, web_session_id):
        service = self.create_service(self.web_session_model)
        service.filter('web_session_id', 'eq', web_session_id)
        return getattr(service.read(), 'user_id', None)


class AuthorizationService(AuthenticationService):
    def __init__(self, user_role_model, *args, **kwargs):
        self.user_role_model = user_role_model
        super(AuthorizationService, self).__init__(*args, **kwargs)

    def has_perm(self, uid, controller, action):
        service = self.create_service(self.user_role_model)
        service.filter('user_id', 'eq', uid)
        service.filter('permission.controller', 'eq', controller)
        service.filter('permission.action', 'eq', action)

        return service.read() is not None