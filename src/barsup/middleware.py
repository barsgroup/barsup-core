# coding: utf-8
"""
API-middleware
"""

from datetime import datetime
from sys import stderr


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


def transact(session):
    """
    Транзакционная mw, оборачивает запрос в транзакцию
    """

    def wrapper(nxt, controller, action, **params):
        try:
            result = nxt(controller, action, **params)
            session.commit()
        except Exception:
            session.rollback()
            raise
        else:
            return result

    return wrapper
