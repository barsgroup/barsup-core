# coding: utf-8

from functools import wraps

from barsup.container import Injectable
from barsup.serializers import to_dict


def commit(f):
    @wraps(f)
    def inner(self, *args, **kwargs):
        result = f(self, *args, **kwargs)
        self.service.session.commit()
        return result

    return inner


class DictController(object):
    __metaclass__ = Injectable
    __slots__ = ['service', 'uid']
    depends_on = ('service',)

    actions = (
        (r"/create", "create", {'records': 'list'}),

        (r"/read", "read", {
            'start': 'int',
            'limit': 'int',
            'page': 'int',
            'filter': 'dict',
            'query': 'unicode'
        }),
        (r"/read/{id_:\d+}", "get"),

        (r"/update", "bulk_update", {'records': 'list'}),
        (r"/update/{id_:\d+}", "update", {'data': 'dict'}),

        (r"/destroy/", "bulk_destroy", {'records': 'list'}),
        (r"/destroy/{id_:\d+}", "destroy",),
    )

    def _init(self):
        # Метода для описания service для правильной подсветки синтаксиса
        self.service = None

    def read(self, start, limit, page,
             query=None, filter=None,
             group=None, sort=None):

        self.service.query('*')
        if filter:
            self.service.filter(**filter)

        if group:
            self.service.filter(**group)

        if sort:
            self.service.filter(**sort)

        self.service.limiter(start, limit)
        return self.service.load()

    def get(self, id_=None):
        self.service.query('*')
        self.service.filter(id=id_)
        return to_dict(self.service.read())

    def _update(self, id_, record):
        self.service.query('*')
        self.service.filter(id=id_)
        obj = self.service.read()
        self.service.update(obj, **record)

        # TODO: плохо, но иначе объект имеет старые связи
        # FIXME: коммит вывести на уровень сервисов
        self.service.session.commit()
        return obj

    @commit
    def bulk_update(self, records):
        return map(to_dict, [self._update(record['id'], record) for record in records])

    @commit
    def update(self, id_, data):
        return map(to_dict, [self._update(id_, data)])

    def _destroy(self, id_):
        self.service.query('*')
        self.service.filter(id=id_)
        obj = self.service.read()
        self.service.delete(obj)

    @commit
    def bulk_destroy(self, identifiers):
        for id_ in identifiers:
            self._destroy(id_)
        return identifiers

    @commit
    def destroy(self, id_):
        self._destroy(id_)
        return id_

    @commit
    def create(self, records):
        new_records = []
        for record in records:
            # FIXME: Пока "это" необходимо для идентфикации записи
            # на клиенте при отправке результата
            client_id = record.pop('id')
            new_record = self.service.create(**record)
            self.service.session.flush()  # FIXME: flush вывести на уровень сервисов
            dict_rec = to_dict(new_record)
            dict_rec['client_id'] = client_id
            new_records.append(dict_rec)
        return new_records