# coding: utf-8
import os

import simplejson as json

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.sql.schema import Table, MetaData, Column, Index


class _BuildMapping:
    @classmethod
    def create_fk(cls, __name__, **kwargs):
        return __name__(**kwargs)

    @classmethod
    def create_column(cls, __name__, __type__, __fk__=None, **kwargs):
        args = [__name__, cls.create_type(**__type__)]
        if __fk__:
            args.append(cls.create_fk(**__fk__))

        return Column(*args, **kwargs)

    @classmethod
    def create_type(cls, __name__, **kwargs):
        return __name__(**kwargs)

    @classmethod
    def load(cls, meta, fname):
        with open(fname, 'r') as f:
            cls.create_table(
                meta,
                json.loads(f.read(), object_hook=cls.cast_type))

    @classmethod
    def create_table(cls, meta, tables):
        for table in tables:
            indices = []
            if table.get('__indices__'):
                indices = [cls.create_indeces(**index) for index in table['__indices__']]

            Table(
                table['__name__'],
                meta,
                *([cls.create_column(**column) for column in table['__columns__']] + indices))

    @classmethod
    def create_indeces(cls, __name__, __columns__, **kwargs):
        return Index(__name__, *__columns__, **kwargs)

    @classmethod
    def cast_type(cls, obj):
        items = []
        for k, v in obj.items():
            if isinstance(v, str) and v.startswith('$'):
                v = getattr(sqlalchemy, v[1:])
            elif isinstance(v, dict):
                v = cls.cast_type(v)
            items.append((k, v))
        return dict(items)


class Model:
    ASTERISK = "*"

    JOIN_CONDITIONS = {
        '==': 'join',
        '=': 'outerjoin'
    }

    def __init__(self, db_mapper, session, name,
                 joins=None, select=ASTERISK):
        self._db_mapper = db_mapper
        self._name = name
        self._session = session

        qs = self._create_select(session, select,
                                 [outher[0] for *_, outher in joins or []])

        self._qs = self._create_joins(qs, joins or [])

    def _create_aliases(self, model_name=''):
        model = getattr(self._db_mapper, model_name, self.current)
        for column in inspect(model).attrs:
            if isinstance(column, ColumnProperty):
                yield self._create_alias(column.key, model_name)

    def _create_alias(self, field, model_name=''):
        model = getattr(self._db_mapper, model_name, self.current)

        col = getattr(model, field)
        if model_name:
            label = col.label('{0}.{1}'.format(model_name, field))
        else:
            label = col.label(field)
        return label

    def _create_select(self, session, select, models):
        select_statement = []
        if select == self.ASTERISK:
            # select * from ...
            select_statement.extend(
                self._create_aliases()
            )
            # Нужно собрать информацию с джойнов
            for m in models:
                select_statement.extend(self._create_aliases(m))
        else:
            # select id, foo, bar from baz
            for field in select:
                names = field.split('.')
                if len(names) == 2:
                    model, column = names
                else:
                    model, column = '', field

                select_statement.append(
                    self._create_alias(column, model))

        assert select_statement
        return session.query(*select_statement)

    def create_query(self):
        return self._qs

    def create_object(self, *args, **kwargs):
        obj = self.current(*args, **kwargs)
        for item, value in kwargs.items():
            assert hasattr(obj, item)
            setattr(obj, item, value)

        self._session.add(obj)
        self._session.flush()  # Для получения id объекта
        return obj.id

    def get_field(self, field_name, model_name=None):
        if model_name:
            model = getattr(self._db_mapper, model_name)
        else:
            model = self.current

        return getattr(model, field_name)

    def _create_joins(self, qs, joins):
        for inner_field_name, condition, outher_field_name, outher in joins:
            # TODO: Реализовать вложенные джойны
            outer_model_name = outher[0]  #

            operator = getattr(qs, self.JOIN_CONDITIONS[condition])
            outer_model = getattr(self._db_mapper, outer_model_name)
            qs = operator(
                outer_model,
                self.get_field(inner_field_name) == self.get_field(outher_field_name, outer_model_name))

        return qs

    @property
    def current(self):
        return getattr(self._db_mapper, self._name)


class DBMapper:
    """
    Коллекция mappings для моделей из приложений,
    указанных при вызове конструктора
    """

    def __init__(self, path=None):
        if not path:
            path = os.path.abspath('.')

        fullpath = os.path.join(path, 'mapping.json')

        self._metadata = MetaData()
        _BuildMapping.load(self._metadata, fullpath)

        self._base = automap_base(metadata=self._metadata)
        self._base.prepare()

    def __getattr__(self, attr):
        return getattr(self._base.classes, attr)


__all__ = (DBMapper, Model)