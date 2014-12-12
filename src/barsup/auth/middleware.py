# coding: utf-8


def access_check(authentication, authorization=None):
    """
    Middleware, проверяющая наличие session id среди параметров.
    При этом web_session_id дальше не передается.

    :param authentication: controller аутентификации
    :type authentication: str

    :param authorization: controller авторизации
    :type authorization: str
    """

    NEED_LOGIN = 'need-login'
    NOT_PERMIT = 'not-permit'

    def wrapper(nxt, controller, action, web_session_id, **params):
        if controller == authentication:
            return nxt(controller, action, web_session_id=web_session_id, **params)
        else:
            # пользователь должен быть аутентифицирован
            uid = nxt(authentication, 'is_logged_in', web_session_id=web_session_id)
            if not uid:
                return False, NEED_LOGIN

            # пользователь должен иметь право на выполнение действия
            if authorization and not nxt(
                    authorization, 'has_perm', uid=uid, operation=(controller, action)
            ):
                return False, NOT_PERMIT

            return nxt(controller, action, **params)

    return wrapper