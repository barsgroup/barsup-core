# coding: utf-8
from barsup.exceptions import Unauthorized, Forbidden, NotFound


def access_check(authentication, authorization=None):
    """
    Middleware, проверяющая наличие session id среди параметров.
    При этом web_session_id дальше не передается.

    :param authentication: controller аутентификации
    :type authentication: str

    :param authorization: controller авторизации
    :type authorization: str
    """

    # NEED_LOGIN = 'need-login'
    # NOT_PERMIT = 'not-permit'

    def wrapper(nxt, controller, action, web_session_id, **params):
        if controller == authentication:
            return nxt(controller, action, web_session_id=web_session_id, **params)
        else:
            # пользователь должен быть аутентифицирован
            try:
                uid = nxt(authentication, 'is_logged_in', web_session_id=web_session_id)
            except NotFound:
                raise Unauthorized()

            # пользователь должен иметь право на выполнение действия
            if authorization and not nxt(
                authorization, 'has_perm', uid=uid, operation=(controller, action)
            ):
                raise Forbidden()

            return nxt(controller, action, **params)

    return wrapper