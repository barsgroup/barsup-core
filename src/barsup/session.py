# coding: utf-8
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session


class DefaultSession(object):
    def __init__(self, connection):
        self._session = Session(
            create_engine(connection, echo=True))

    def __getattr__(self, item):
        return getattr(self._session, item)