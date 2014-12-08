# coding: utf-8

import operator
import weakref

from sqlalchemy.sql import expression, operators

from barsup.serializers import to_dict, convert


def _mapping_property(f):
    """
    Декоратор, возвращающий объект sqlalchemy по составному имени поля
    """

    def wrapper(self, property, *args, **kwargs):
        names = property.split('.')
        if len(names) == 2:  # Составной объект, например, user.name
            outer_model, column = names
            model = getattr(self.service.db_mapper, outer_model)
        else:
            model, column = self.service.model, property

        return f(self, getattr(model, column), *args, **kwargs)

    return wrapper


def _filter(column, operator_text, value):
    values = {
        'like': {
            'type': operators.ilike_op,
            'format': '%{0}%'
        },
        'eq': operator.eq,
        'lt': operator.lt,
        'le': operator.le,
        'gt': operator.gt,
        'ge': operator.ge,
        'in': operators.in_op
    }

    assert operator_text in values.keys()
    oper = values[operator_text]
    if isinstance(oper, dict):
        func = oper['type']
        value = oper['format'].format(value)
    else:
        func = oper

    return func(column, value)


def _sorter(direction):
    values = {
        'ASC': expression.asc,
        'DESC': expression.desc
    }
    assert direction in values.keys()
    return values[direction]


def _delegate_proxy(name):
    def wrap(self, *args, **kwargs):
        return _Proxy(self.service, self.queue + [(name, args, kwargs)])

    return wrap


def _delegate_service(name):
    def wrap(self, *args, **kwargs):
        method = getattr(self.service, name)
        return method(_QuerySetBuilder(self.service).build(self.queue), *args, **kwargs)

    return wrap


class _Proxy:
    def __init__(self, service, queue=None):
        self.service = service
        self.queue = queue or []

    filter = _delegate_proxy('_filter')
    filters = _delegate_proxy('_filters')
    filter_by_id = _delegate_proxy('_filter_by_id')

    sort = _delegate_proxy('_sort')
    sorts = _delegate_proxy('_sorts')

    limiter = _delegate_proxy('_limit')

    get = _delegate_service('_get')
    read = _delegate_service('_read')

    update = _delegate_service('_update')
    delete = _delegate_service('_delete')


class _QuerySetBuilder:
    apply_filter = staticmethod(_filter)
    apply_sorter = staticmethod(lambda x, y: _sorter(y)(x))

    def __init__(self, service):
        self.service = service
        self._qs = self._create_qs()

    def _create_qs(self):
        return self.service.session.query(
            self.service.model
        )

    def build(self, queue):
        for item, args, kwargs in queue:
            getattr(self, item)(*args, **kwargs)
        return self._qs

    # FILTERS:
    @_mapping_property
    def _filter(self, property, operator, value):
        self._qs = self._qs.filter(
            self.apply_filter(
                property,
                operator,
                convert(property, value)))

    def _filters(self, filters):
        for filter_ in filters:
            self._filter(**filter_)

    def _filter_by_id(self, id_):
        self._filter('id', 'eq', id_)

    # SORTERS:
    @_mapping_property
    def _sort(self, property, direction):
        sort = self.apply_sorter(property, direction)
        self._qs = self._qs.order_by(sort)

    def _sorts(self, sorts):
        for sort in sorts:
            self._sort(**sort)

    def _limit(self, offset, limit):
        self._qs = self._qs.limit(limit).offset(offset)


class Service:
    def __init__(self,
                 model,
                 session,
                 db_mapper,
                 models=None,
                 joins=None,
                 select=None, ):
        self.model = model
        self.models = models
        self.joins = joins
        self.select = select
        self.session = session
        self.db_mapper = db_mapper

    def __call__(self, model=None):
        self.model = model or self.model
        return _Proxy(weakref.proxy(self))

    def __getattr__(self, item):
        proxy = _Proxy(weakref.proxy(self))
        return getattr(proxy, item)

    def _get(self, qs):
            return qs.scalar()

    def _read(self, qs):
        return map(to_dict, qs.all())

    def _update(self, qs, **kwargs):
        if kwargs:
            params = {}
            for item, value in kwargs.items():
                value = self._deserialize(item, value)

                params[item] = value
            qs.update(params)

            return qs.scalar()

    def _delete(self, qs):
        qs.delete()

    # For create
    def _deserialize(self, item, value):
        return convert(
            getattr(self.model, item), value)

    def _initialize(self, **kwargs):
        obj = self.model()
        for item, value in kwargs.items():
            assert hasattr(obj, item)
            value = self._deserialize(item, value)
            setattr(obj, item, value)
        return obj

    def create(self, **kwargs):
        obj = self._initialize(**kwargs)
        self.session.add(obj)

        # Для получения id объекта - flush
        self.session.flush()
        return obj


__all__ = (Service,)