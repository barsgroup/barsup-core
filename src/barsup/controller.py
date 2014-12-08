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

        service = self.service()
        if filter:
            service = self.service.filters(filter)

        if sort:
            service = service.sorts(sort)

        if start is not None and limit is not None:
            service = service.limiter(start, limit)

        return service.read()

    def get(self, id_, filter=None):

        service = self.service.filter_by_id(id_)
        if filter:
            service = service.filters(filter)

        return to_dict(service.get())

    def _update(self, id_, record):
        return self.service.filter_by_id(id_).update(**record)

    def bulk_update(self, records):
        return map(to_dict,
                   [self._update(record['id'], record) for record in records])

    def update(self, id_, data):
        return map(to_dict, [self._update(id_, data)])

    def _destroy(self, id_):
        self.service.filter_by_id(id_).delete()

    def bulk_destroy(self, identifiers):
        for id_ in identifiers:
            self._destroy(id_)
        return identifiers

    def destroy(self, id_):
        self._destroy(id_)
        return id_

    def _create(self, record):
        return self.service.create(**record)

    def create(self, records):
        return map(to_dict, (self._create(record) for record in records))


__all__ = (DictController,)
