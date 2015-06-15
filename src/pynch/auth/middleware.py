# coding: utf-8
"""Набор MW для аутентификации/авторизации."""

import pynch.exceptions as exc


def authentication(auth, white_list=None):
    """
    MW для аутентификации.

    :param auth: сервис аутентфикации
    :param preserve_user: список контроллеров,
    которые должны получать пользователя
    :param white_list: Список контроллеров без проверки
    :return: вызов следующей по списку MW
    """
    bypass = set(white_list or []).__contains__

    def wrapper(nxt, controller, action, _web_session_id=None, **params):
        if bypass(controller):
            return nxt(
                controller, action, _web_session_id=_web_session_id,
                **params
            )
        try:
            uid = auth.is_logged_in(web_session_id=_web_session_id)
        except exc.NotFound:
            raise exc.Unauthorized()

        params['_context'].setdefault('uid', uid)
        return nxt(controller, action, **params)

    return wrapper


def authorization(auth, preserve_user=None, white_list=None):
    """
    MW для авторизации.

    :param auth: сервис авторизации
    :param white_list: Список контроллеров без проверки
    :return: вызов следующей по списку MW
    """
    bypass = set(white_list or []).__contains__

    def wrapper(nxt, controller, action, **params):
        if bypass(controller):
            return nxt(controller, action, **params)

        uid = params['_context']['uid']
        # _subroute - проверка прав только на конечных узлах
        if 'subroute' not in params:
            if controller in (preserve_user or []):
                params['_uid'] = uid

            qualified_controller = '/'.join(
                [i[0] for i in params['_context'].get('path', [])] +
                [controller]
            )
            if not auth.has_perm(uid, qualified_controller, action):
                raise exc.Forbidden(uid, qualified_controller, action)
        return nxt(controller, action, **params)

    return wrapper
