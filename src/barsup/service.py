# coding: utf-8

from datetime import date
import operator

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import expression, operators

import barsup.exceptions as exc
from barsup.service_adapter import ADAPTERS


def _mapping_property(f):
    """
    Декоратор, возвращающий объект sqlalchemy по составному имени поля
    """

    def wrapper(self, property, *args, **kwargs):
        names = property.split('.')
        if len(names) == 2:  # Составной объект, например, user.name
            outer_model, column = names
            field = self._model.get_field(column, outer_model)
        else:
            field = self._model.get_field(property)

        return f(self, field, *args, **kwargs)

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

    if operator_text not in values.keys():
        raise exc.NameValidationError('Operator "{0}" not supported. Available operators: [{1}]'.format(
            operator_text,
            ', '.join(values.keys())
        ))

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
    if direction not in values.keys():
        raise exc.NameValidationError('Direction "{0}" not supported. Available directions: [{1}]'.format(
            direction,
            ', '.join(values.keys())
        ))
    return values[direction]


def _delegate_proxy(name):
    def wrap(self, *args, **kwargs):
        return self.create_proxy(
            self._callback,
            self._model,
            self.queue + [(name, args, kwargs)])

    return wrap


def _delegate_service(name):
    def wrap(self, *args, **kwargs):
        return self._callback(name)(
            self.query_builder(
                self._model
            ).build(
                self.queue
            ), *args, **kwargs)

    return wrap


class _QuerySetBuilder:
    apply_filter = staticmethod(_filter)
    apply_sorter = staticmethod(lambda x, y: _sorter(y)(x))

    def __init__(self, model):
        self._model = model
        self._qs = self._create_qs()

    def _create_qs(self):
        return self._model.create_query()

    def build(self, queue):
        for item, args, kwargs in queue:
            getattr(self, item)(*args, **kwargs)
        return self._qs

    # FILTERS:
    @_mapping_property
    def _filter(self, property, operator, *args, **kwargs):
        if args or kwargs:
            if kwargs:
                value = kwargs['value']
            if args:
                value = args[0]

            self._qs = self._qs.filter(
                self.apply_filter(
                    property,
                    operator,
                    Serializer.to_record(property, value)))

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
        if offset is not None:
            self._qs = self._qs.offset(offset)
        if limit is not None:
            self._qs = self._qs.limit(limit)


class _Proxy:
    query_builder = _QuerySetBuilder

    def __init__(self, callback, model, queue=None):
        self._callback = callback
        self._model = model
        self.queue = queue or []

    @classmethod
    def create_proxy(cls, *args, **kwargs):
        return cls(*args, **kwargs)

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


class Serializer:
    @staticmethod
    def to_record(field, value):
        type_ = field.type
        if issubclass(type_.python_type, date):
            if len(str(value)) == 13:  # timestamp c милисекундами
                value /= 1000.0
            value = date.fromtimestamp(float(value))
        return value

    @staticmethod
    def from_record(value):
        if isinstance(value, date):
            return date.strftime(value, '%m/%d/%Y')
        return value


class View:
    serialization = staticmethod(Serializer.to_record)
    deserialization = staticmethod(Serializer.from_record)

    def __init__(self, view, current_model):
        self._adapters = view.get('adapters', [])
        self._include = view.get('include', [])
        self._exclude = view.get('exclude', [])
        self._current_model = current_model

    @property
    def adapters(self):
        for adapter_name, name, from_names, kwargs in self._adapters:
            yield ADAPTERS[adapter_name](name, from_names, **kwargs)

        yield ADAPTERS['default'](self._current_model,
                                  self._include, self._exclude)

    def from_record(self, params):
        """
        Controller <- Model

        Правило работы:
        Deserialization <- Include/Exclude <- Adapters

        :param params:
        :return:
        """
        result = {}
        for adapter in self.adapters:
            result, params = adapter.from_record(result, params)

        return {name: self.deserialization(value) for name, value in result.items()}

    def to_record(self, params):
        """
        Controller -> Model

        Правило работы:
        Include/Exclude -> Adapters -> Serialization -> Validation

        :param params:
        :return:
        """

        # Преобразования на уровне адаптеров
        result = {}
        for adapter in self.adapters:
            result, params = adapter.to_record(result, params)

        new_params = {}
        for name, value in result.items():
            field = getattr(self._current_model, name)

            # Серриализация перед валидацией
            value = self.serialization(field, value)

            # Умолчательная валидация на уровне типов значений
            self.validation(field, value)

            new_params[name] = value

        return new_params

    @staticmethod
    def validation(field, value):

        if value is None:
            if field.expression.nullable:
                return
            else:
                raise exc.NullValidationError('Field "{0}" can not be null'.format(
                    field.key
                ))

        if not isinstance(value, field.type.python_type):
            raise exc.TypeValidationError('Field "{0}" must be {1} type, but has value "{2}"'.format(
                field.key, field.type.python_type, value
            ))

        if hasattr(field.type, 'length') and len(value) > field.type.length:
            raise exc.LengthValidationError('Field "{0}" must be length "{1}", but has "{3}" for "{2}"'.format(
                field.key, field.type.length, value, len(value)
            ))


class Service:
    to_dict = staticmethod(lambda o: o._asdict())

    def __init__(self, model, view):
        self._model = model
        self._adapter = View(view, model.current)

    def __call__(self, model=None):
        return _Proxy(
            callback=lambda name: self.__getattribute__(name),
            model=model or self._model)

    def __getattr__(self, item):
        proxy = _Proxy(
            callback=lambda name: self.__getattribute__(name),
            model=self._model)
        return getattr(proxy, item)

    def _get(self, qs):
        try:
            record = qs.one()
        except NoResultFound:
            raise exc.NotFound()

        return self._adapter.from_record(
            self.to_dict(record)
        )

    def _read(self, qs):
        return map(
            self._adapter.from_record,
            map(self.to_dict, qs.all())
        )

    def _update(self, qs, **kwargs):
        if kwargs:
            params = {}
            for item, value in kwargs.items():
                value = self._deserialize(item, value)

                params[item] = value

            qs.with_entities(self._model.current).update(
                self._adapter.to_record(params)
            )
            return self._adapter.from_record(
                self.to_dict(qs.one())
            )

    def _delete(self, qs):
        qs.with_entities(self._model.current).delete()

    # For create & update
    def _deserialize(self, item, value):
        return Serializer.to_record(self._model.get_field(item), value)

    def create(self, **kwargs):
        # params = {k: self._deserialize(k, v) for k, v in kwargs.items()}
        id_ = self._model.create_object(
            **self._adapter.to_record(kwargs)
        )
        return self.filter('id', 'eq', id_).get()


__all__ = (Service,)