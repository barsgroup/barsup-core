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
            model = getattr(self._db_mapper, outer_model)
        else:
            model, column = self._model, property

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


class _Query:
    serialize = staticmethod(to_dict)
    deserialize = staticmethod(convert)

    apply_filter = staticmethod(_filter)
    apply_sorter = staticmethod(lambda x, y: _sorter(y)(x))


    def __init__(self, qs, model, session, db_mapper):
        self._qs = qs
        self._model = model
        self._session = session
        self._db_mapper = db_mapper

    def filters(self, filters):
        for filter_data in filters:
            self.filter(**filter_data)

    @_mapping_property
    def filter(self, property, operator, value):
        self._qs = self._qs.filter(
            self.apply_filter(property, operator,
                              self.deserialize(property, value)))

    def grouper(self, *args):
        self._qs = self._qs.group_by(*args)

    def sorters(self, sorters):
        for sorter in sorters:
            self.sorter(**sorter)

    @_mapping_property
    def sorter(self, property, direction):
        sort = self.apply_sorter(property, direction)
        self._qs = self._qs.order_by(sort)

    def _load(self):
        return self._qs.all()

    def load(self):
        return map(self.serialize, self._load())

    def limiter(self, offset, limit):
        self._qs = self._qs.limit(limit).offset(offset)

    # Record methods
    def create(self, **kwargs):
        instance = self._initialize(**kwargs)
        self._session.add(instance)

        # Для получения id объекта - flush
        self._session.flush()
        return instance

    def read(self):
        return self._qs.scalar()

    def update(self, **kwargs):
        params = {}
        for item, value in kwargs.items():
            value = self.deserialize(
                getattr(self._model, item), value)

            params[item] = value
        if params:
            self._qs.update(params)

    def delete(self):
        self._qs.delete()

    def _initialize(self, **kwargs):
        obj = self._model()
        for item, value in kwargs.items():
            assert hasattr(obj, item)
            value = self.deserialize(getattr(self._model, item), value)
            setattr(obj, item, value)
        return obj

    def filter_by_id(self, value):
        self.filter(
            property='id',
            operator='eq',
            value=value)

    @classmethod
    def create_query(cls, model, db_mapper, joins, session, entire='*', *args):

        if entire == '*':
            qs = session.query(model)
        else:
            qs = session.query(
                *map(lambda x: getattr(model, x), args)
            )

        model_joins = joins.get(model.__name__, [])
        assert isinstance(model_joins, (list, tuple))
        for join in model_joins:
            if ':' in join:
                method, model_name = join.split(':')
            else:
                method, model_name = 'join', join

            qs_method = getattr(qs, method)
            qs = qs_method(getattr(db_mapper, model_name))

        return cls(qs, model, session, db_mapper)


class Query:
    ENTIRE = '*'

    CONDITION_VALUES = {
        '==': 'join',
        '=': 'outerjoin'
    }

    def __init__(self, key=None, entire=ENTIRE):
        self.key = key
        self.entire = entire

    def __get__(self, obj, objtype):
        joins = obj.joins and obj.joins.get(self.key)

        if joins:
            from_model, *from_model_params = joins
            fmodel = getattr(obj, from_model)
            query = self.create_query(obj.session, fmodel)
            for from_field, condition, to_field, *to_model_list in from_model_params:
                for to_model, *to_model_params in to_model_list:
                    assert condition in self.CONDITION_VALUES.keys()
                    oper = getattr(query, self.CONDITION_VALUES[condition])

                    tmodel = getattr(obj, to_model)
                    query = oper(tmodel, getattr(fmodel, from_field) == getattr(tmodel, to_field))

        else:
            query = self.create_query(obj.session, obj.model)
        return query

    def create_query(self, session, model, *args):
        if self.entire == self.ENTIRE:
            qs = session.query(model)
        else:
            qs = session.query(
                *map(lambda x: getattr(model, x), args)
            )
        return qs


class Service(metaclass=Injectable):
    depends_on = ('model', 'session', 'db_mapper', 'joins')

    query = Query('default')

    def __init__(self, model, session, db_mapper, joins=None):
        self.model = model
        self.session = session
        self.db_mapper = db_mapper
        self.joins = joins

    def __enter__(self):
        return self.create_service(self.model)

    def __exit__(self, exc_type, exc_val, exc_tb):
        return

    def get(self, id_):
        _query = self.create_service(self.model)
        _query.filter_by_id(id_)
        return _query

    def create_service(self, model, query=None):
        self.model = model
        query = query or self.query

        return _Query(
            model=model,
            db_mapper=self.db_mapper,
            qs=query,
            session=self.session,
        )


__all__ = (Service, )



