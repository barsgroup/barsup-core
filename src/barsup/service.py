# coding: utf-8
import operator
from sqlalchemy.sql import expression, operators

from barsup.serializers import to_dict, convert
from barsup.container import Injectable


def mapping_property(f):
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
            'format': u'%{0}%'
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


class Service(object):
    __metaclass__ = Injectable
    depends_on = ('model', 'session', 'db_mapper', 'joins')
    __slots__ = depends_on + ('_queryset',)

    serialize = staticmethod(to_dict)
    deserialize = staticmethod(convert)

    apply_filter = staticmethod(_filter)
    apply_sorter = staticmethod(lambda x, y: _sorter(y)(x))

    def __init(self):
        self.session = self.model = self.joins = self.db_mapper = None

    def query(self, *args):
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
                getattr(self.db_mapper, model)
            )

    def filters(self, filters):
        for filter_data in filters:
            self.filter(**filter_data)

    @mapping_property
    def filter(self, property, operator, value):
        self._queryset = self._queryset.filter(
            self.apply_filter(
                property,
                operator,
                self.deserialize(property, value)
            )
        )

    def grouper(self, *args):
        self._queryset = self._queryset.group_by(*args)

    def sorters(self, sorters):
        for sorter in sorters:
            self.sorter(**sorter)

    @mapping_property
    def sorter(self, property, direction):
        sort = self.apply_sorter(
            property,
            direction)
        self._queryset = self._queryset.order_by(sort)

    def _load(self):
        return self._queryset.all()

    def load(self):
        return map(self.serialize, self._load())

    def limiter(self, offset, limit):
        self._queryset = self._queryset.limit(limit).offset(offset)

    # Record methods
    def create(self, **kwargs):
        instance = self._init(self.model(), **kwargs)
        self.session.add(instance)
        return instance

    def read(self):
        return self._queryset[0]

    def update(self, obj, **kwargs):
        for item, value in kwargs.items():
            assert hasattr(obj, item)
            value = self.deserialize(
                getattr(self.model, item), value)
            setattr(obj, item, value)

        self.session.add(obj)

    def delete(self, obj):
        self.session.delete(obj)

    def _init(self, obj, **kwargs):
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
