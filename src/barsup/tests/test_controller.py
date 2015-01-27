# coding: utf-8

import pytest

from barsup.controller import DictController
from barsup.core import init, ModuleContainer
from barsup.service import _Proxy


class Result(dict):
    def _asdict(self):
        return self


class _QueryBuilder:
    def __init__(self, *args, **kwargs):
        pass

    def _filters(self, *args, **kwargs):
        pass

    def _filter(self, *args, **kwargs):
        pass

    def _filter_by_id(self, *args, **kwargs):
        pass

    def _sorts(self, *args, **kwargs):
        pass

    def _limiter(self, *args, **kwargs):
        pass

    def build(self, *args, **kwargs):
        pass


class Proxy(_Proxy):
    query_builder = _QueryBuilder


class Service:
    def __call__(self, *args, **kwargs):
        return Proxy(
            model=None,
            callback=lambda name: self.__getattribute__(name)
        )

    def __getattr__(self, item):
        query = Proxy(
            model=None,
            callback=lambda name: self.__getattribute__(name)
        )
        return getattr(query, item)

    #
    def _read(self, *args, **kwargs):
        return []

    def _get(self, *args, **kwargs):
        return Result()

    def _update(self, *args, **kwargs):
        return Result()

    def create(self, *args, **kwargs):
        return Result()

    def _delete(self, *args, **kwargs):
        pass


class LocalContainer(ModuleContainer):
    def _get_entity(self, name):
        try:
            return {
                'local.Controller': DictController
            }[name]
        except KeyError:
            return super(LocalContainer, self)._get_entity(name)


@pytest.fixture
def get_api():
    api = init({'controller': {
        'cont': {
            '__realization__': 'local.Controller',
            '$service': Service()
        }
    }, }, container_clz=LocalContainer, get_config=lambda x: x)
    return api


def test_read():
    read_result = get_api().call('cont', 'read', )
    read_result = list(read_result)
    assert isinstance(read_result, list)


def test_get():
    get_result = get_api().call('cont', 'get', id_=5)
    assert isinstance(get_result, dict)


def test_update():
    update_result = get_api().call('cont', 'update', id_=10, data={})
    assert isinstance(update_result, dict)


def test_create():
    create_result = get_api().call('cont', 'create', data={})
    assert isinstance(create_result, dict)


def test_destroy():
    destroy_result = get_api().call('cont', 'destroy', id_=15)
    assert isinstance(destroy_result, int)
    assert destroy_result == 15
