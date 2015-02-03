# coding: utf-8
"""Преднастроенные конструкции для всех тестов."""

import os

from barsup.core import init
from barsup.schema import DBMapper


class DBMapperMock(DBMapper):

    """Mock маппера БД."""

    def __init__(self, session, path):
        """.

        :param session: Сессия к БД
        :param path: Путь до конфигурационного файла схемы БД
        :return:
        """
        test_path = os.path.dirname(__file__)
        super().__init__(os.path.join(test_path, *path))
        self.session = session
        self.create_tables()
        self.create_data()

    def create_tables(self):
        """
        Создание тестовых таблиц.

        :return:
        """
        for name, table in self._metadata.tables.items():
            table.create(self.session.engine)

    def create_data(self):
        """
        Создание тестовых данных.

        :return:
        """
        pass


def create_api(*path):
    """
    Декоратор для создания API.

    :param path: Путь до файла контейнера
    :return:
    """
    def inner(f):
        def wrap(*args, **kwargs):
            test_path = os.path.join(os.path.dirname(__file__), *path)
            api = init(config=test_path)
            return f(api, *args, **kwargs)
        return wrap
    return inner
