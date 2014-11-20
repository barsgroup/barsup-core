# coding: utf-8
from datetime import date
from sqlalchemy.sql.expression import asc, desc
from barsup.serializers import to_dict
from barsup.container import Injectable


def _sorter(direction):
    values = {
        'ASC': asc,
        'DESC': desc
    }
    assert direction in (values.keys())
    return values[direction]


class Service(object):
    __metaclass__ = Injectable

    serialize = staticmethod(to_dict)
    depends_on = ('model', 'session', 'db_mapper', 'joins')

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

    def filter(self, **kwargs):
        self._queryset = self._queryset.filter(
            *(getattr(self.model, param) == value
              for param, value in kwargs.items())
        )

    def grouper(self, *args):
        self._queryset = self._queryset.group_by(*args)

    def sorters(self, sorters):
        for sorter in sorters:
            self.sorter(**sorter)

    def sorter(self, property, direction):
        # Сложный объект
        names = property.split('.')
        if len(names) == 2:
            outer_model, column = names
            model = getattr(self.db_mapper, outer_model)
        else:
            model, column = self.model, property

        sort = _sorter(direction)(getattr(model, column))
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
            value = self._prepare(item, value)
            setattr(obj, item, value)

        self.session.add(obj)

    def delete(self, obj):
        self.session.delete(obj)

    def _init(self, obj, **kwargs):
        for item, value in kwargs.items():
            assert hasattr(obj, item)
            value = self._prepare(item, value)
            setattr(obj, item, value)
        return obj

    def _prepare(self, item, value):
        """
        Преобразование входящих значений согласно типам колонок

        :param item: Наименование поля
        :param value: Значение поля
        :return: Преобразованное значение
        """
        type_ = getattr(self.model, item).type
        if issubclass(type_.python_type, date):
            return date.fromtimestamp(float(value))
        return value