# coding: utf-8

import os
import json

from barsup.core import init
from barsup.mapping import DBMapper


class DBMapperMock(DBMapper):
    def __init__(self, session, path):
        test_path = os.environ.get('BUP_TESTS')
        super().__init__(os.path.join(test_path, *path))
        self.session = session
        self.create_tables()
        self.create_data()

    def create_tables(self):
        for name, table in self._metadata.tables.items():
            table.create(self.session.engine)

    def create_data(self):
        pass


def create_api(*path):
    def inner(f):
        def wrap(*args, **kwargs):
            test_path = os.environ.get('BUP_TESTS')
            with open(os.path.join(test_path, *path)) as conf:
                api = init(
                    config=json.load(conf)['container']
                )
                return f(api, *args, **kwargs)

        return wrap

    return inner
