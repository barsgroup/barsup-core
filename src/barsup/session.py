# coding: utf-8
"""Различные реализации уровня сессии.

В том числе реализация по настройке подключения к БД
"""

from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session


class InMemory:

    """Подключение к SQLite в памяти."""

    def __init__(self):
        """."""
        self.engine = create_engine('sqlite://', echo=True)
        self.session = Session(self.engine)

    def __getattr__(self, item):
        """Прозрачная работа с объектом Session.

        :param item: атрибут для доступа
        :return:
        """
        return getattr(self.session, item)


class PostgreSQLSession:

    """Подключение к PostgreSQL."""

    def __init__(
        self,
        login,
        password,
        database,
        engine='postgresql',
        host='localhost',
        port=5432,
        echo=True
    ):
        """Конструирует сессию для PostgreSQL.

        :param login: Логин
        :param password: Пароль
        :param database: Название БД
        :param engine: Тип подключения
        :param host: Хост
        :param port: Порт
        :param echo: Логировать ли информацию
        """
        connection_string = (
            '{engine}://'
            '{login}:{password}'
            '@{host}:{port}/'
            '{database}'
        ).format(
            login=login,
            password=password,
            database=database,
            engine=engine,
            host=host,
            port=port
        )
        engine = create_engine(connection_string, echo=echo)
        self.session = Session(engine)

    def __getattr__(self, item):
        """Прозрачная работа с объектом Session.

        :param item: атрибут для доступа
        :return:
        """
        return getattr(self.session, item)


__all__ = ('PostgreSQLSession', 'InMemory')
