# coding: utf-8

import pytest

import barsup.exceptions as exc
from barsup.tests import create_api


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


get_api = create_api('api', 'api.json')


@get_api
def test_empty_read(api):
    data = api.call('SimpleController', 'read')
    # assert isinstance(data, Iterable)
    assert len(list(data)) == 0


@get_api
def test_empty_filter(api):
    data = api.call(
        'SimpleController', 'read',
        filter=[
            {'property': 'name', 'operator': 'eq', 'value': 'Test test'}
        ], start=0, limit=100
    )
    # assert isinstance(data, Iterable)
    assert len(list(data)) == 0


@get_api
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


@get_api
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


@get_api
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

    # assert isinstance(data, Iterable)
    assert len(list(data)) == 0


@get_api
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


@get_api
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


@get_api
def test_wrong_sort_name(api):
    with pytest.raises(exc.NameValidationError):
        api.call(
            'SimpleController', 'read',
            limit=1,
            sort=[{'property': 'not_real_name', 'direction': 'DESC'}]
        )


@get_api
def test_wrong_sort_direction(api):
    with pytest.raises(exc.ValidationError):
        api.call(
            'SimpleController', 'read',
            limit=1,
            sort=[{'property': 'name', 'direction': 'desc'}]
        )


@get_api
def test_wrong_filter_operator(api):
    with pytest.raises(exc.ValidationError):
        api.call(
            'SimpleController', 'read',
            filter=[
                {'property': 'name', 'operator': '=', 'value': 'Test test'}
            ], start=0, limit=100
        )


@get_api
def test_not_found_record(api):
    with pytest.raises(exc.NotFound):
        api.call(
            'SimpleController', 'get', id_=1
        )


@get_api
def test_create_overflow_name(api):
    with pytest.raises(exc.LengthValidationError):
        api.call(
            'SimpleController', 'create',
            data={
                'name': '42' * 100
            }
        )


@get_api
def test_create_nullable_name(api):
    with pytest.raises(exc.NullValidationError):
        api.call(
            'SimpleController', 'create',
            data={
                'name': None
            }
        )


@get_api
def test_create_wrong_type_name(api):
    with pytest.raises(exc.TypeValidationError):
        api.call(
            'SimpleController', 'create',
            data={
                'name': {"complex": "type"}
            }
        )


@get_api
def test_create_wrong_value_with_adapters(api):
    with pytest.raises(exc.AdapterException):
        api.call(
            'AdapterController', 'create', data={
                'name': 'atata' * 5,
                'full_name': "Complex field"
            }
        )


@get_api
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


@get_api
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


@get_api
@generate_master_detail_series
def test_complex_filter_detail(api):
    data = api.call(
        "Detail", "read",
        filter=[
            {'property': 'master.name',
             'operator': 'like',
             'value': '1'},
            {'property': 'name',
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
@get_api
@generate_master_detail_series
def test_delete_with_fk(api):
    data = api.call(
        "Detail", "read", filter=[
            {'property': 'master_id',
             'operator': 'eq',
             'value': 1}]
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
             'value': 1}
        ]
    )
    data = list(data)
    assert len(data) == 0  # Записи удалились


@get_api
def test_date(api):
    from datetime import datetime as dt
    import time

    timestamp = time.time()  # текущий timestamp
    format_ = '%m/%d/%Y'  # такой странный формат

    data = api.call(
        'Types', 'create',
        data={
            'date': timestamp
        }
    )

    assert data
    assert data['date'] == dt.fromtimestamp(timestamp).strftime(format_)


@get_api
def test_create_with_wrong_data(api):
    with pytest.raises(exc.NameValidationError):
        api.call(
            'SimpleController', 'create',
            data={
                'anothername': '42'
            }
        )


@get_api
def test_create_without_constraint_field(api):
    with pytest.raises(exc.ValidationError):
        api.call(
            'SimpleController', 'create',
            data={}
        )


@get_api
def test_without_params(api):
    with pytest.raises(TypeError):
        api.call(
            'SimpleController', 'create',
        )
