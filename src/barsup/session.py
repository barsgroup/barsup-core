# coding: utf-8
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session


class DefaultSession(object):
    __slots__ = ('session', )

    def __init__(self, connection):
        engine = create_engine(connection, echo=True)
        self.session = Session(engine)

    def __getattr__(self, item):
        return getattr(self.session, item)