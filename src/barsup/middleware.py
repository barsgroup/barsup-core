# coding: utf-8
"""API-middleware."""

from datetime import datetime
from sys import stderr


def _timestamped(s):
    """'asd' -> 2014/12/12|08:30:45|asd."""
    return "%s|%s" % (
        datetime.now().strftime("yyyy/mm/dd|HH:MM:SS"), s)


def log_errors_to_stderr(nxt, controller, action, **params):
    """Middleware, выводящая ошибки вызова API в STDERR."""
    if '_subroute' in params:  # Конечный узел
        return nxt(controller, action, **params)
    else:
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
    """Транзакционная mw, оборачивает запрос в транзакцию."""
    def _transact(f, *args, **kwargs):
        try:
            result = f(*args, **kwargs)
            session.commit()
        except Exception:
            session.rollback()
            raise
        else:
            return result

    def wrapper(nxt, controller, action, **params):
        if 'in_transaction' in params['_context']:  # Конечный узел
            return nxt(controller, action, **params)
        else:
            params['_context']['in_transaction'] = True
            return _transact(nxt, controller, action, **params)

    return wrapper
