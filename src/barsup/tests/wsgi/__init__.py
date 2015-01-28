# coding: utf-8
from barsup.router import RoutingError
import barsup.exceptions as exc


class MockAPI:
    def __init__(self, *args, **kwargs):
        pass

    def populate(self, key, **params):
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
