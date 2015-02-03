# coding: utf-8
"""Вспомогательные конструкции для тестов WSGI."""

from barsup.router import RoutingError
import barsup.exceptions as exc


class MockAPI:

    """Заглушка для API."""

    def __init__(self, *args, **kwargs):
        """Игнорирует входящие параметры."""
        pass

    def populate(self, key, **params):
        """
        Возвращает набор предустановленных значений по ключам URL.

        :param key:
        :param params:
        :return:
        """
        result = {
            '/wrong-controller': RoutingError(),
            '/controller/with_data': params,
            '/unauthorized': exc.Unauthorized(),
            '/forbidden': exc.Forbidden(1, 'test', 'test'),
            '/not-found': exc.NotFound(),
            '/value-error': ValueError(),
            '/wrong-serialize': object(),
        }[key]

        if isinstance(result, Exception):
            raise result
        else:
            return result
