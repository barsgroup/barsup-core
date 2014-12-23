# coding: utf-8
from _collections_abc import Iterable

import pytest
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql.schema import MetaData

import barsup.exceptions as exc
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


def create_api(f):
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
                        },
                        "nullable": False
                    },
                    {
                        "__name__": "lname",
                        "__type__": {
                            "__name__": sqlalchemy.String,
                            "length": 50
                        },
                        "nullable": True
                    }, {
                        "__name__": "oname",
                        "__type__": {
                            "__name__": sqlalchemy.String,
                            "length": 50
                        },
                        "nullable": True
                    }
                ]
            }, {
                "__name__": "master",
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
                        },
                        "nullable": False
                    }
                ]
            },
            {
                "__name__": "detail",
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
                        },
                        "nullable": False
                    },
                    {
                        "__name__": "master_id",
                        "__type__": {
                            "__name__": sqlalchemy.Integer
                        },
                        "__fk__": {
                            "__name__": sqlalchemy.ForeignKey,
                            "column": "master.id",
                            "ondelete": "RESTRICT"
                        },
                        "nullable": False
                    },
                ]
            },
            {
                "__name__": "types",
                "__columns__": [
                    {
                        "__name__": "id",
                        "__type__": {
                            "__name__": sqlalchemy.Integer
                        },
                        "primary_key": True
                    },
                    {
                        "__name__": "date",
                        "__type__": {
                            "__name__": sqlalchemy.Date
                        },
                        "nullable": False
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
                "AdapterController": {
                    "service": "AdapterService"
                },
                "Master": {
                    "service": "MasterService"
                },
                "Detail": {
                    "service": "DetailService"
                },
                "Types": {
                    "service": "TypesService"
                }
            },
            "service": {
                "__default__": {
                    "__realization__": "barsup.service.Service",
                    "adapters": []
                },
                "MasterService": {
                    "model": "master"
                },
                "DetailService": {
                    "model": "detail"
                },
                "SimpleService": {
                    "model": "simple_model"
                },
                "TypesService": {
                    "model": "types"
                },
                "AdapterService": {
                    "adapters": [
                        "AdapterSplitter"
                    ],
                    "$include": ["id", "full_name", "name"],
                    "$exclude": ["oname", "lname"],
                    "model": "simple_model"
                }
            },
            "adapters": {
                "AdapterSplitter": {
                    "__realization__": "barsup.adapters.Splitter",
                    "$to_name": "full_name",
                    "$from_names": ["lname", "oname"],
                    "$sep": ", "
                }
            },
            "model": {
                "__default__": {
                    "__realization__": "barsup.mapping.Model",
                    "db_mapper": "default",
                    "session": "default"
                },
                "simple_model": {
                    "$name": "simple_table"
                },
                "detail": {
                    "$name": "detail",
                    "$joins": [
                        ["master_id", "==", "id", ["master", []]],
                    ],
                    "$select": [
                        "id",
                        "master_id",
                        "name"
                    ]
                },
                "master": {
                    "$name": "master"
                },
                "types": {
                    "$name": "types"
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
                    "__realization__":
                        "barsup.tests.test_integration._DBMapperMock",
                    "__type__": "singleton",
                    "$tables": _tables,
                    "session": "default"
                }
            },
            "api_options": {
                "default": {
                    "middleware": [
                    ]
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


def generate_series(f):
    def wrap(api, *args, **kwargs):
        for i in range(100):
            api.call(
                'SimpleController', 'create',
                data={
                    'name': 'data {0}'.format(i)
                }
            )
        return f(api, *args, **kwargs)

    return wrap


@create_api
def test_empty_read(api):
    data = api.call('SimpleController', 'read')
    assert isinstance(data, Iterable)
    assert len(list(data)) == 0


@create_api
def test_empty_filter(api):
    data = api.call(
        'SimpleController', 'read',
        filter=[
            {'property': 'name', 'operator': 'eq', 'value': 'Test test'}
        ], start=0, limit=100
    )
    assert isinstance(data, Iterable)
    assert len(list(data)) == 0


@create_api
def test_create(api):
    data = api.call(
        'SimpleController', 'create',
        data={
            'name': '42'
        }
    )

    assert data['name'] == '42'
    assert data['id'] == 1

    data = api.call(
        'SimpleController', 'get',
        id_=1)

    assert data['name'] == '42'
    assert data['id'] == 1


@create_api
def test_update(api):
    api.call(
        'SimpleController', 'create',
        data={
            'name': 'one record'
        }
    )

    data = api.call(
        'SimpleController', 'update',
        id_=1, data={
            'name': 'updated record'
        })

    assert data['name'] == 'updated record'
    assert data['id'] == 1

    data = api.call(
        'SimpleController', 'get',
        id_=1)

    assert data['name'] == 'updated record'
    assert data['id'] == 1


@create_api
def test_delete(api):
    api.call(
        'SimpleController', 'create',
        data={
            'name': 'one record'
        }
    )

    data = api.call(
        'SimpleController', 'destroy', id_=1)

    assert data == 1

    data = api.call(
        'SimpleController', 'read')

    assert isinstance(data, Iterable)
    assert len(list(data)) == 0


@create_api
@generate_series
def test_read(api):
    data = api.call(
        'SimpleController', 'read',
        start=10, limit=15
    )
    data = list(data)

    assert len(data) == 15
    for i, j in enumerate(range(10, 25)):
        assert 'data {0}'.format(j) == data[i]['name']


@create_api
@generate_series
def test_sorts(api):
    data = api.call(
        'SimpleController', 'read',
        limit=1,
        sort=[{'property': 'name', 'direction': 'DESC'}]
    )
    data = list(data)

    assert len(data) == 1
    assert data[0]['name'] == 'data 99'


@create_api
def test_wrong_sort_name(api):
    with pytest.raises(exc.NameValidationError):
        api.call(
            'SimpleController', 'read',
            limit=1,
            sort=[{'property': 'not_real_name', 'direction': 'DESC'}]
        )


@create_api
def test_wrong_sort_direction(api):
    with pytest.raises(exc.NameValidationError):
        api.call(
            'SimpleController', 'read',
            limit=1,
            sort=[{'property': 'name', 'direction': 'desc'}]
        )


@create_api
def test_wrong_filter_operator(api):
    with pytest.raises(exc.NameValidationError):
        api.call(
            'SimpleController', 'read',
            filter=[
                {'property': 'name', 'operator': '=', 'value': 'Test test'}
            ], start=0, limit=100
        )


@create_api
def test_not_found_record(api):
    with pytest.raises(exc.NotFound):
        api.call(
            'SimpleController', 'get', id_=1
        )


@create_api
def test_create_overflow_name(api):
    with pytest.raises(exc.LengthValidationError):
        api.call(
            'SimpleController', 'create',
            data={
                'name': '42' * 100
            }
        )


@create_api
def test_create_nullable_name(api):
    with pytest.raises(exc.NullValidationError):
        api.call(
            'SimpleController', 'create',
            data={
                'name': None
            }
        )


@create_api
def test_create_wrong_type_name(api):
    with pytest.raises(exc.TypeValidationError):
        api.call(
            'SimpleController', 'create',
            data={
                'name': {"complex": "type"}
            }
        )


@create_api
def test_create_wrong_value_with_adapters(api):
    with pytest.raises(exc.ValueValidationError):
        api.call(
            'AdapterController', 'create', data={
                'name': 'atata' * 5,
                'full_name': "Complex field"
            }
        )


@create_api
def test_create_with_adapters(api):
    api.call(
        'AdapterController', 'create', data={
            'name': 'atata' * 5,
            'full_name': "Complex, field"
        }
    )

    data = api.call(
        'AdapterController', 'get', id_=1
    )

    assert isinstance(data, dict)
    assert data.get('full_name', None)
    assert data['full_name'] == "Complex, field"


@create_api
def test_create_with_wrong_name_adapters(api):
    with pytest.raises(exc.NameValidationError):
        api.call(
            'AdapterController', 'create', data={
                'name': 'atata' * 5,
                'atata': "Yet another value",
                'full_name': "Complex, field"
            }
        )


def generate_master_detail_series(f):
    def wrap(api, *args, **kwargs):
        for i in range(10):
            master = api.call(
                'Master', 'create',
                data={
                    'name': 'master {0}'.format(i)
                }
            )
            for j in range(20):
                api.call(
                    'Detail', 'create',
                    data={
                        'name': 'master {0}; detail {1}'.format(i, j),
                        'master_id': master['id']
                    }
                )
        return f(api, *args, **kwargs)

    return wrap


@create_api
@generate_master_detail_series
def test_complex_filter_detail(api):
    data = api.call(
        "Detail", "read",
        filter=[
            {'property': 'master.name',
             'operator': 'like',
             'value': '1'
            }, {
                'property': 'name',
                'operator': 'like',
                'value': '2'}
        ]
    )
    data = list(data)
    assert len(data) == 2
    assert data[0]['name'] == 'master 1; detail 2'
    assert data[1]['name'] == 'master 1; detail 12'


# В sqlite тест ниже не работает с параметром RESTRICT
# Видимо, всегда работает как каскадное (CASCADE) удаление
@create_api
@generate_master_detail_series
def test_delete_with_fk(api):
    data = api.call(
        "Detail", "read", filter=[
            {'property': 'master_id',
             'operator': 'eq',
             'value': 1
            }]
    )
    data = list(data)
    assert len(data) == 20  # 20 дочерних записей

    # Должно было упасть с BadRequest, так как на master есть ссылки
    # Вместо этого sqlite делает каскадное удаление
    api.call(
        "Master", "destroy", id_=1
    )

    with pytest.raises(exc.NotFound):
        api.call(
            "Master", "get", id_=1
        )

    data = api.call(
        "Detail", "read", filter=[
            {'property': 'master_id',
             'operator': 'eq',
             'value': 1
            }]
    )
    data = list(data)
    assert len(data) == 0  # Записи удалились

@create_api
def test_date(api):
    data = api.call(
        'Types', 'create',
        data={
            'date': 1419341293000  # timestamp
        }
    )

    assert data
    assert data['date'] == '12/23/2014'