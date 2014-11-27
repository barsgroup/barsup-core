# coding: utf-8
import operator
from sqlalchemy.sql import expression, operators
from yadic import Injectable

from barsup.serializers import to_dict, convert

def _mapping_property(f):
    """
    Декоратор, возвращающий объект sqlalchemy по составному имени поля
    """

    def wrapper(self, property, *args, **kwargs):
        names = property.split('.')
        if len(names) == 2:  # Составной объект, например, user.name
            outer_model, column = names
            model = getattr(self.db_mapper, outer_model)
        else:
            model, column = self.model, property

        return f(self, property=getattr(model, column), *args, **kwargs)

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


class _Query:
    serialize = staticmethod(to_dict)
    deserialize = staticmethod(convert)

    apply_filter = staticmethod(_filter)
    apply_sorter = staticmethod(lambda x, y: _sorter(y)(x))

    def _init(self):
        # Данный метод не вызывается
        # он необходим для правильной подсветки синтаксиса
        # т. к. синтаксические анализаторы не понимают внедренные зависимости
        self._queryset = self.session = self.model = self.joins = self.db_mapper = None

    def __init__(self, *args):
        if '*' in args:
            self._queryset = self.session.query(self.model)
        else:
            self._queryset = self.session.query(
                *map(lambda x: getattr(self.model, x), args)
            )

        for join in self.joins:
            if ':' in join:
                method, model = join.split(':')
            else:
                method, model = 'join', join

            qs_method = getattr(self._queryset, method)
            self._queryset = qs_method(
                getattr(self.db_mapper, model))

    def filters(self, filters):
        for filter_data in filters:
            self.filter(**filter_data)

    @_mapping_property
    def filter(self, property, operator, value):
        self._queryset = self._queryset.filter(
            self.apply_filter(property, operator,
                              self.deserialize(property, value)))

    def grouper(self, *args):
        self._queryset = self._queryset.group_by(*args)

    def sorters(self, sorters):
        for sorter in sorters:
            self.sorter(**sorter)

    @_mapping_property
    def sorter(self, property, direction):
        sort = self.apply_sorter(property, direction)
        self._queryset = self._queryset.order_by(sort)

    def _load(self):
        return self._queryset.all()

    def load(self):
        return map(self.serialize, self._load())

    def limiter(self, offset, limit):
        self._queryset = self._queryset.limit(limit).offset(offset)

    # Record methods
    def create(self, **kwargs):
        instance = self._initialize(self.model(), **kwargs)
        self.session.add(instance)

        # Для получения id объекта - flush
        self.session.flush()
        return instance

    def read(self):
        return self._queryset[0]  # FIXME: заменять на .scalar()

    def update(self, **kwargs):
        params = {}
        for item, value in kwargs.items():
            value = self.deserialize(
                getattr(self.model, item), value)

            params[item] = value
        self._queryset.update(params)

    def delete(self):
        self._queryset.delete()

    def _initialize(self, obj, **kwargs):
        for item, value in kwargs.items():
            assert hasattr(obj, item)
            value = self.deserialize(
                getattr(self.model, item), value)
            setattr(obj, item, value)
        return obj

    def filter_by_id(self, value):
        self.filter(
            property='id',
            operator='eq',
            value=value)


class Service(metaclass=Injectable):
    depends_on = ('model', 'session', 'db_mapper', 'joins')
    # __slots__ = depends_on + ('query_cls', )

    def __init__(self, **kwargs):
        self.query_cls = type('NewQuery', (_Query,), kwargs)

    def __enter__(self):
        return self.query_cls('*')

    def __exit__(self, exc_type, exc_val, exc_tb):
        return

    def get(self, id_):
        q = self.query_cls('*')
        q.filter_by_id(id_)
        return q


__all__ = (Service, )