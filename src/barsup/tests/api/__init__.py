# coding: utf-8
import os
from barsup.mapping import DBMapper


class _DBMapperMock(DBMapper):
    def __init__(self, session):
        super().__init__(os.path.join('tests', 'api', 'schema.json'))
        self.create(session.engine)

    def create(self, engine):
        for name, table in self._metadata.tables.items():
            table.create(engine)