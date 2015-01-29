# coding: utf-8
import barsup.exceptions as exc


def access_check(authentication, authorization=None, preserve_user=None):
    """
    Middleware, проверяющая наличие session id среди параметров.
    При этом web_session_id дальше не передается.

    :param authentication: controller аутентификации
    :type authentication: str

    :param authorization: controller авторизации
    :type authorization: str
    """

    def wrapper(nxt, controller, action, web_session_id=None, **params):
        if '_subroute' in params:
            def _auth_check(*args, **kwargs):
                return nxt(*args, **kwargs)

            params['_context']['_auth_check'] = _auth_check

        if not web_session_id and 'uid' not in params['_context']:
            raise exc.BadRequest("web session must be defined")

        if controller == authentication:
            return nxt(controller, action,
                       web_session_id=web_session_id, **params)
        else:
            # пользователь должен быть аутентифицирован
            if 'uid' not in params['_context']:
                try:
                    uid = nxt(authentication, 'is_logged_in',
                              web_session_id=web_session_id)
                except exc.NotFound:
                    raise exc.Unauthorized()

                params['_context']['uid'] = uid

            if params['_context']['uid'] and '_subroute' not in params:
                uid = params['_context']['uid']
                auth_check = params['_context'].get('_auth_check', nxt)
                # пользователь должен иметь право на выполнение действия
                if authorization and not auth_check(
                    authorization, 'has_perm', uid=uid,
                    operation=(controller, action)
                ):
                    raise exc.Forbidden(uid, controller, action)

                if controller in (preserve_user or []):
                    params['uid'] = uid

            return nxt(controller, action, **params)

    return wrapper
