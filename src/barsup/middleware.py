# coding: utf-8
"""
API-middleware
"""

from datetime import datetime
from sys import stderr
from barsup.exceptions import NeedLogin

NEED_LOGIN = 'need_login'


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


def authentificate(controller):
    """
    Middleware, проверяющая наличие session id среди параметров.
    При этом web_session_id дальше не передается
    """
    auth_controller = controller

    def wrapper(nxt, controller, *args, **params):
        if auth_controller.__class__.__name__ == controller:
            return nxt(controller, *args, **params)
        else:
            if not auth_controller.is_logged_in(params.pop('web_session_id')):
                return False, NEED_LOGIN

            return nxt(controller, *args, **params)

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