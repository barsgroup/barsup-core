# coding: utf-8

from yadic.container import Injectable
from barsup.serializers import to_dict


class DictController(metaclass=Injectable):
    """
    Представляет уровень контроллера

    Инжектирует в себя:
        - service - компонент, отвечающий за уровень сервиса
        - uid - идентификатор соединения

    Выполняет задачи:
        - Декларация и проверка на тип входящих параметров
        - ...

    """

    depends_on = ('service',)
    __slots__ = depends_on + ('uid',)

    actions = (
        (r"/create", "create", {'records': 'list'}),

        (r"/read", "read", {
            'start': 'int',
            'limit': 'int',
            'page': 'int',
            'filter': 'json',
            'query': 'str',
            'sort': 'json'
        }),
        (r"/read/{id_:\d+}", "get", {
            'filter': 'json'
        }),

        (r"/update", "bulk_update", {'records': 'list'}),
        (r"/update/{id_:\d+}", "update", {'data': 'dict'}),

        (r"/destroy/", "bulk_destroy", {'records': 'list'}),
        (r"/destroy/{id_:\d+}", "destroy",),
    )

    def _init(self):
        # Данный метод не вызывается
        # он необходим для правильной подсветки синтаксиса
        # т. к. синтаксические анализаторы не понимают внедренные зависимости
        self.service = None

    def read(self, start=None, limit=None, page=None,
             query=None, filter=None,
             group=None, sort=None):

        with self.service as service:

            if filter:
                service.filters(filter)

            if group:
                service.filter(**group)

            if sort:
                service.sorters(sort)

            if start and limit:
                service.limiter(start, limit)

            return service.load()

    def get(self, id_, filter=None):
        with self.service as service:
            service.filter_by_id(id_)
            if filter:
                service.filters(filter)
            return to_dict(service.read())

    def _update(self, id_, record):
        with self.service as service:
            service.filter_by_id(id_)
            service.update(**record)

            obj = service.read()
        return obj

    def bulk_update(self, records):
        return map(to_dict,
                   [self._update(record['id'], record) for record in records])

    def update(self, id_, data):
        return map(to_dict, [self._update(id_, data)])

    def _destroy(self, id_):
        self.service.get(id_).delete()

    def bulk_destroy(self, identifiers):
        for id_ in identifiers:
            self._destroy(id_)
        return identifiers

    def destroy(self, id_):
        self._destroy(id_)
        return id_

    def _create(self, record):
        with self.service as service:
            return service.create(**record)

    def create(self, records):
        return map(to_dict, (self._create(record) for record in records))


__all__ = (DictController,)
