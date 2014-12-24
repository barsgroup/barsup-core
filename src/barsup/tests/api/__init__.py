# coding: utf-8
import os
from os import path
from barsup.mapping import DBMapper


class _DBMapperMock(DBMapper):
    def __init__(self, session):
        test_path = path.expandvars('$BUP_TESTS')
        super().__init__(os.path.join(test_path, 'api', 'schema.json'))
        self.create(session.engine)

    def create(self, engine):
        for name, table in self._metadata.tables.items():
            table.create(engine)