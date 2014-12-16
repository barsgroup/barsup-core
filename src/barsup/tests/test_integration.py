# coding: utf-8
from _collections_abc import Iterable
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql.schema import MetaData
from barsup.core import init
from barsup.mapping import DBMapper, _BuildMapping


class _DBMapperMock(DBMapper):
    def __init__(self, session, tables):
        self._metadata = MetaData()
        _BuildMapping.create_table(
            self._metadata, tables
        )
        self._base = automap_base(metadata=self._metadata)
        self._base.prepare()
        self.create(session.engine)

    def create(self, engine):
        for name, table in self._metadata.tables.items():
            table.create(engine)


def api(f):
    def wrap(*args, **kwargs):
        _tables = [
            {
                "__name__": "simple_table",
                "__columns__": [
                    {
                        "__name__": "id",
                        "__type__": {
                            "__name__": sqlalchemy.Integer
                        },
                        "primary_key": True
                    },
                    {
                        "__name__": "name",
                        "__type__": {
                            "__name__": sqlalchemy.String,
                            "length": 50
                        }
                    }
                ]
            },
        ]

        api = init({
            'controller': {
                "__default__": {
                    "__realization__": "barsup.controller.DictController"
                },
                "SimpleController": {
                    "service": "SimpleService"
                },
            },
            "service": {
                "__default__": {
                    "__realization__": "barsup.service.Service"
                },
                "SimpleService": {
                    "model": "simple_model"
                },
            },
            "model": {
                "__default__": {
                    "__realization__": "barsup.mapping.Model",
                    "db_mapper": "default",
                    "session": "default"
                },
                "simple_model": {
                    "$name": "simple_table"
                }
            },
            "session": {
                "default": {
                    "__type__": "singleton",
                    "__realization__": "barsup.session.InMemory"
                }
            },
            "db_mapper": {
                "default": {
                    "__realization__": "barsup.tests.test_integration._DBMapperMock",
                    "__type__": "singleton",
                    "$tables": _tables,
                    "session": "default"
                }
            },
            "api_options": {
                "default": {
                    "middleware": [
                        "wrap_result"
                    ]
                }
            },
            "middleware": {
                "__default__": {"__type__": "static"},
                "wrap_result": {
                    "__realization__": "barsup.middleware.wrap_result"
                }
            },
            "runtime": {
                "__default__": {"__type__": "static"},
                "actions": {
                    "__realization__": "barsup.runtime.ACTIONS"
                }
            }
        })
        return f(api, *args, **kwargs)

    return wrap


@api
def test_empty_read(api):
    status, data = api.call('SimpleController', 'read')
    assert status is True
    assert isinstance(data, Iterable)
    assert len(list(data)) == 0


@api
def test_empty_filter(api):
    status, data = api.call(
        'SimpleController', 'read',
        filter=[
            {'property': 'name', 'operator': 'eq', 'value': 'Test test'}
        ], start=0, limit=100
    )
    assert status is True
    assert isinstance(data, Iterable)
    assert len(list(data)) == 0


@api
def test_create(api):
    status, data = api.call(
        'SimpleController', 'create',
        data={
            'name': 'one record'
        }
    )
    assert status is True
    assert data['name'] == 'one record'
    assert data['id'] == 1

    status, data = api.call(
        'SimpleController', 'get',
        id_=1)

    assert status is True
    assert data['name'] == 'one record'
    assert data['id'] == 1


@api
def test_update(api):
    api.call(
        'SimpleController', 'create',
        data={
            'name': 'one record'
        }
    )

    status, data = api.call(
        'SimpleController', 'update',
        id_=1, data={
            'name': 'updated record'
        })

    assert status is True
    assert data['name'] == 'updated record'
    assert data['id'] == 1

    status, data = api.call(
        'SimpleController', 'get',
        id_=1)

    assert status is True
    assert data['name'] == 'updated record'
    assert data['id'] == 1


@api
def test_delete(api):
    api.call(
        'SimpleController', 'create',
        data={
            'name': 'one record'
        }
    )

    status, data = api.call(
        'SimpleController', 'destroy', id_=1)

    assert status is True
    assert data == 1

    status, data = api.call(
        'SimpleController', 'read')

    assert status is True
    assert isinstance(data, Iterable)
    assert len(list(data)) == 0