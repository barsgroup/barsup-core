# coding: utf-8

from functools import wraps

from barsup.container import Injectable

from barsup.serializers import to_dict
from barsup.session import DefaultSession


def commit(f):
    @wraps(f)
    def inner(self, *args, **kwargs):
        result = f(self, *args, **kwargs)
        DefaultSession.get().commit()
        return result
    return inner


class DictController(object):
    __metaclass__ = Injectable
    depends_on = ('service',)

    actions = (
        ("/read", "read"),
        ("/create", "create"),
        ("/update", "update"),
        ("/destroy", "destroy"),
        (r"/{_id:\d+}/get", "get"),
    )

    def load(self, start, limit, **params):
        self.service.query('*')
        if params.get('filter'):
            self.service.filter(**params['filter'])

        if params.get('group'):
            self.service.filter(**params['group'])

        if params.get('sort'):
            self.service.filter(**params['sort'])

        self.service.limiter(start, limit)

        return self.service.load()

    def read(self, params, **kwargs):
        return self.load(**params)

    def get(self, _id, **kwargs):
        self.service.query('*')
        self.service.filter(id=_id)
        return to_dict(self.service.read())

    @commit
    def update(self, params, **kwargs):
        records = []
        for record in params:
            self.service.query('*')
            self.service.filter(id=record['id'])
            obj = self.service.read()
            self.service.update(obj, **record)

            DefaultSession.get().commit()  # TODO: плохо, но иначе объект имеет старые связи
            records.append(obj)
        return map(to_dict, records)

    @commit
    def destroy(self, params, **kwargs):
        for record in params:
            self.service.query('*')
            self.service.filter(id=record['id'])
            obj = self.service.read()
            self.service.delete(obj)
        return params

    @commit
    def create(self, params, **kwargs):
        new_records = []
        for record in params:
            # FIXME: Пока "это" необходимо для идентфикации записи
            # на клиенте при отправке результата
            client_id = record.pop('id')
            new_record = self.service.create(**record)
            DefaultSession.get().flush()
            dict_rec = to_dict(new_record)
            dict_rec['client_id'] = client_id
            new_records.append(dict_rec)
        return new_records
