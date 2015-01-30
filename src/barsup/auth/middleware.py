# coding: utf-8
import barsup.exceptions as exc


def authentication(auth, preserve_user=None):
    """
    MW для аутентификации

    :param auth: контроллер аутентфикации
    :param preserve_user: список контроллеров,
    которые должны получать пользователя
    :return: вызов следующей по списку MW
    """
    def wrapper(nxt, *args, web_session_id=None, **params):
        controller, action = args
        if auth.__class__.__name__ == controller:
            method = getattr(auth, action)
            params.pop('_context')
            return method(web_session_id=web_session_id, **params)

        try:
            uid = auth.is_logged_in(web_session_id=web_session_id)
        except exc.NotFound:
            raise exc.Unauthorized()

        params['_context'].setdefault('uid', uid)
        if controller in (preserve_user or []):
            params['uid'] = uid
        return nxt(*args, **params)

    return wrapper


def authorization(auth):
    """
    MW для авторизации

    :param auth: контроллер авторизации
    :return: вызов следующей по списку MW
    """
    def wrapper(nxt, *args, **params):
        uid = params['_context']['uid']
        # _subroute - проверка прав только на конечных узлах
        if (not params.get('_subroute') and
                not auth.has_perm(uid=uid, operation=args)):
            raise exc.Forbidden(uid, *args)

        return nxt(*args, **params)

    return wrapper
