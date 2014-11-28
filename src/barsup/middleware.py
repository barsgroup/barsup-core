# coding: utf-8
"""
API-middleware
"""

from datetime import datetime
from sys import stderr

NEED_LOGIN = 'need-login'
NOT_PERMIT = 'not-permit'


def _timestamped(s):
    """
    'asd' -> 2014/12/12|08:30:45|asd
    """
    return "%s|%s" % (
        datetime.now().strftime("yyyy/mm/dd|HH:MM:SS"), s)


def log_errors_to_stderr(nxt, controller, action, **params):
    """
    Middleware, выводящая ошибки вызова API в STDERR
    """
    try:
        return nxt(controller, action, **params)
    except Exception as exc:
        stderr.write(_timestamped(
            "{controller}:{action}({params}) -> Error: \"{exc}\"".format(
                controller=controller,
                action=action,
                params=','.join('%s=%r' % p for p in params.items()),
                exc=exc
            )))
        raise


def access_check(controller):
    """
    Middleware, проверяющая наличие session id среди параметров.
    При этом web_session_id дальше не передается
    """
    auth_controller = controller
    has_perm = getattr(controller, 'has_perm', lambda *a, **k: True)

    def wrapper(nxt, controller, action, **params):
        if auth_controller.__class__.__name__ == controller:
            return nxt(controller, action, **params)
        else:
            uid = auth_controller.is_logged_in(params.pop('web_session_id'))
            if not uid:
                return False, NEED_LOGIN

            if not has_perm(uid, controller, action):
                return False, NOT_PERMIT

            return nxt(controller, action, **params)

    return wrapper


def transact(session):
    """
    Транзакционная mw, оборачивает запрос в транзакцию
    """

    def wrapper(nxt, *args, **params):
        try:
            result = nxt(*args, **params)
            session.commit()
        except Exception:
            session.rollback()
            raise
        else:
            return result

    return wrapper


def wrap_result(nxt, *args, **kwargs):
    result = nxt(*args, **kwargs)
    if not (isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], bool)):
        return True, result
    else:
        return result