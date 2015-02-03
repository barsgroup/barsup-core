# coding: utf-8
"""Набор конструкция для работы с уровнем моделей."""
import os

import simplejson as json
import sqlalchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.sql.schema import Table, MetaData, Column, Index

import barsup.exceptions as exc


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
                indices = [cls.create_indeces(**index) for index in
                           table['__indices__']]

            Table(
                table['__name__'],
                meta,
                *([cls.create_column(**column) for column in
                   table['__columns__']] + indices))

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

    """Реализация уровня модели."""

    # Аналогично select *
    ASTERISK = "*"

    # Возможные операции соединения
    JOIN_CONDITIONS = {
        '==': 'join',
        '=': 'outerjoin'
    }

    def __init__(self, db_mapper, session, name,
                 joins=None, select=ASTERISK):
        """.

        :param db_mapper: Ссылка на маппер
        :param session: Ссылка на сессию
        :param name: Название таблицы
        :param joins: Список таблиц для соединения
        :param select: Список полей для селекта или select *
        """
        self._db_mapper = db_mapper
        self._name = name
        self._session = session
        self._labels = {}

        qs = self._create_select(session, select,
                                 [outher[0] for *_, outher in joins or []])

        self._qs = self._create_joins(qs, joins or [])

    def _create_aliases(self, model_name=''):
        # Создание алиасов, чтобы джойны не пересекались
        model = getattr(self._db_mapper, model_name, self.current)
        for column in inspect(model).attrs:
            if isinstance(column, ColumnProperty):
                yield self._create_alias(column.key, model_name)

    def _create_alias(self, field, model_name=''):
        # Создание алиаса для конкретного поля в модели,
        # если модель не используется - предполагается текущая модель
        model = getattr(self._db_mapper, model_name, self.current)

        col = getattr(model, field)
        if model_name:
            key = '{0}.{1}'.format(model_name, field)
        else:
            key = field

        label = col.label(key)
        self._labels[key] = label

        return label

    def _create_select(self, session, select, models):
        # Создание полей в объекте select
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
        """Работа с запросами."""
        return self._qs

    def create_object(self, **kwargs):
        """Операция создания объекта."""
        obj = self.current()
        for item, value in kwargs.items():
            if not hasattr(obj, item):
                raise exc.NameValidationError(
                    item, obj
                )
            setattr(obj, item, value)

        self._session.add(obj)
        try:
            self._session.flush()  # Для получения id объекта
        except IntegrityError as e:
            # TODO: Перенести проверку на constraint-ов в NullValidationError
            raise exc.ValidationError(
                str(e.orig)
            )
        return obj

    def get_field(self, field_name):
        """
        Получение объекта поля по его наименованию.

        :param field_name: Наименование поля
        """
        # Если есть джойны, тогда должны быть алиасы:
        # alias = self._labels.get(field_name, None)
        # if alias is not None:
        # return alias

        model_name = None
        if '.' in field_name:
            model_name, field_name = field_name.split('.')

        if model_name:
            model = getattr(self._db_mapper, model_name)
        else:
            model = self.current

        try:
            field = getattr(model, field_name)
        except AttributeError:
            raise exc.NameValidationError(
                field_name,
                model
            )

        return field

    def _create_joins(self, qs, joins):
        # Создание join-ов
        for inner_field_name, condition, outher_field_name, outher in joins:
            # TODO: Реализовать вложенные джойны
            outer_model_name = outher[0]  #

            operator = getattr(qs, self.JOIN_CONDITIONS[condition])
            outer_model = getattr(self._db_mapper, outer_model_name)
            qs = operator(
                outer_model,
                self.get_field(inner_field_name) == self.get_field(
                    '{0}.{1}'.format(outer_model_name, outher_field_name)
                ))

        return qs

    @property
    def current(self):
        """Возвращает текущую таблицу."""
        return getattr(self._db_mapper, self._name)

    def exists(self, qs):
        """
        Возвращает QS.

        C присоединенной информацией о проверки наличия объекта
        """
        return self._session.query(qs.exists())


class DBMapper:

    """
    Коллекция mappings для моделей из приложений.

    Которые указываются при вызове конструктора
    """

    def __init__(self, config):
        """.

        :param config: Путь до конфигурации схемы
        :return:
        """
        path = os.path.expandvars(config)
        if not os.path.isfile(path):
            raise ValueError(
                '$BUP_SCHEMA is not file - "{0}"'.format(path))

        self._metadata = MetaData()
        _BuildMapping.load(self._metadata, path)

        self._base = automap_base(metadata=self._metadata)
        self._base.prepare()

    def __getattr__(self, attr):
        """
        Прозрачная работа с данными таблиц.

        :param str attr: Наименование таблицы
        :return:
        """
        return getattr(self._base.classes, attr)


__all__ = ('DBMapper', 'Model')
