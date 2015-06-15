# coding: utf-8
"""Вспомогательные конструкции для тестов WSGI."""

from pynch.router import RoutingError
import pynch.exceptions as exc


class MockFrontend:

    """Заглушка для Frontend."""

    EXCEPTIONS = {
        '/wrong-controller': RoutingError(),
        '/unauthorized': exc.Unauthorized(),
        '/forbidden': exc.Forbidden(1, 'test', 'test'),
        '/not-found': exc.NotFound(),
        '/value-error': ValueError(),
    }

    def __init__(self, *args, **kwargs):
        """Игнорирует входящие параметры."""
        pass

    def populate(self, method, key, **params):
        """
        Возвращает набор предустановленных значений по ключам URL.

        :param key:
        :param params:
        :return:
        """
        result = self.EXCEPTIONS.get(key)

        if isinstance(result, Exception):
            raise result
        elif key == '/controller/with_data':
            return params
        elif key == '/wrong-serialize':
            return object()
