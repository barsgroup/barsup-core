# coding: utf-8
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session


class InMemory:
    def __init__(self):
        self.engine = create_engine('sqlite://', echo=True)
        self.session = Session(self.engine)

    def __getattr__(self, item):
        return getattr(self.session, item)


class PostgreSQLSession:
    def __init__(self,
                 login,
                 password,
                 database,
                 engine='postgresql',
                 host='localhost',
                 port=5432,
                 echo=True):
        connection_string = ('{engine}://'
                             '{login}:{password}'
                             '@{host}:{port}/'
                             '{database}').format(
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
        return getattr(self.session, item)


__all__ = (PostgreSQLSession, InMemory)