# coding: utf-8
import os

import simplejson as json

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql.schema import Table, MetaData, Column, Index


class BuildMapping:
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


def get_model(db_mapper, name):
    """
    Извлекает модель по имени из маппера
    """
    return getattr(db_mapper, name)


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
        BuildMapping.load(self._metadata, fullpath)

        self._base = automap_base(metadata=self._metadata)
        self._base.prepare()

    def __getattr__(self, attr):
        return getattr(self._base.classes, attr)


__all__ = (DBMapper, get_model)