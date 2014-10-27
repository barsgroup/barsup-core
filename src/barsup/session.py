# coding: utf-8
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session


class DefaultSession(object):
    _session = Session(create_engine(
        'postgresql://barsup:barsup@localhost:5432/barsup',
        echo=True))

    @classmethod
    def get(cls):
        return cls._session