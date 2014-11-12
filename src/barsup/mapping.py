# coding: utf-8
import json
import os
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql.schema import Table, MetaData, Column


class BuildMapping(object):

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
            cls.create(
                meta,
                json.loads(f.read(), object_hook=cls.cast_type))

    @classmethod
    def create(cls, meta, tables):
        for table in tables:
            Table(
                table['__name__'],
                meta,
                *[cls.create_column(**column)
                  for column in table['__columns__']])

    @classmethod
    def cast_type(cls, obj):
        items = []
        for k, v in obj.items():
            if isinstance(v, basestring) and v.startswith('$'):
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


class DBMapper(object):
    """
    Коллекция mappings для моделей из приложений,
    указанных при вызове конструктора
    """
    def __init__(self):
        self._metadata = MetaData()
        abspath = os.path.abspath('.')

        fullpath = os.path.join(
            abspath,
            'mapping.json'
        )
        if os.path.isfile(fullpath):
                BuildMapping.load(self._metadata, fullpath)

        self._base = automap_base(metadata=self._metadata)
        self._base.prepare()

    def __getattr__(self, attr):
        return getattr(self._base.classes, attr)