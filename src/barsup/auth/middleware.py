# coding: utf-8
"""Набор MW для аутентификации/авторизации."""

import barsup.exceptions as exc


def authentication(auth, preserve_user=None, white_list=None):
    """
    MW для аутентификации.

    :param auth: сервис аутентфикации
    :param preserve_user: список контроллеров,
    которые должны получать пользователя
    :param white_list: Список контроллеров без проверки
    :return: вызов следующей по списку MW
    """
    def wrapper(nxt, controller, action, web_session_id=None, **params):
        if controller in (white_list or []):
            return nxt(controller, action, web_session_id=web_session_id,
                       **params)

        try:
            uid = auth.is_logged_in(web_session_id=web_session_id)
        except exc.NotFound:
            raise exc.Unauthorized()

        params['_context'].setdefault('uid', uid)
        if controller in (preserve_user or []):
            params['uid'] = uid
        return nxt(controller, action, **params)

    return wrapper


def authorization(auth, white_list=None):
    """
    MW для авторизации.

    :param auth: сервис авторизации
    :param white_list: Список контроллеров без проверки
    :return: вызов следующей по списку MW
    """
    def wrapper(nxt, controller, action, **params):
        if controller in (white_list or []):
            return nxt(controller, action, **params)

        uid = params['_context']['uid']
        # _subroute - проверка прав только на конечных узлах
        if (not params.get('_subroute') and
                not auth.has_perm(uid, controller, action)):
            raise exc.Forbidden(uid, controller, action)

        return nxt(controller, action, **params)

    return wrapper
