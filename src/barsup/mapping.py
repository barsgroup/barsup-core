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

    def __init__(self, db_mapper, session, name, joins=None, select=ASTERISK):
        self._db_mapper = db_mapper
        self._name = name

        qs = self._create_select(
            session,
            select,
            [outher[0] for *_, outher in joins or []])
        self._qs = self._create_joins(qs, joins or [])

    def _get_select_by_model(self, model_name=''):
        model = getattr(self._db_mapper, model_name, self.current)
        for column in inspect(model).attrs:
            if isinstance(column, ColumnProperty):
                col = getattr(model, column.key)
                if model_name:
                    label = col.label('{0}.{1}'.format(model_name, column.key))
                else:
                    label = col.label(column.key)
                yield label

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

    def _create_select(self, session, select, models):
        select_statement = []
        if select == self.ASTERISK:
            # select * from ...
            select_statement.extend(
                self._get_select_by_model()
            )
            # Нужно собрать информацию с джойнов
            for m in models:
                select_statement.extend(self._get_select_by_model(m))
        else:
            # select id, foo, bar from baz
            raise RuntimeError("Unsupported operation")

        assert select_statement
        return session.query(*select_statement)

    def create_query(self):
        return self._qs

    def create_object(self, *args, **kwargs):
        return self.current(*args, **kwargs)

    def get_field(self, field_name, model_name=None):
        if model_name:
            model = getattr(self._db_mapper, model_name)
        else:
            model = self.current

        return getattr(model, field_name)

    @property
    def current(self, ):
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