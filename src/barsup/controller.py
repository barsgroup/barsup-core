# coding: utf-8

from functools import wraps

from barsup.container import Injectable
from barsup.serializers import to_dict


# С появлением _Query, эту конструкцию нельзя использовать
# session необходимо доставать по-другому
# def commit(f):
#     @wraps(f)
#     def inner(self, *args, **kwargs):
#         result = f(self, *args, **kwargs)
#         self.service.session.commit()
#         return result
#
#     return inner


class DictController:
    """
    Представляет уровень контроллера

    Инжектирует в себя:
        - service - компонент, отвечающий за уровень сервиса
        - uid - идентификатор соединения

    Выполняет задачи:
        - Декларация и проверка на тип входящих параметров
        - ...

    """

    __metaclass__ = Injectable
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

    # def _init(self):
    #     # Данный метод не вызывается
    #     # он необходим для правильной подсветки синтаксиса
    #     # т. к. синтаксические анализаторы не понимают внедренные зависимости
    #     self.service = None

    def read(self, start, limit, page,
             query=None, filter=None,
             group=None, sort=None):

        with self.service as service:

            if filter:
                service.filters(filter)

            if group:
                service.filter(**group)

            if sort:
                service.sorters(sort)

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

    # @commit
    def bulk_update(self, records):
        return map(to_dict, [self._update(record['id'], record) for record in records])

    # @commit
    def update(self, id_, data):
        return map(to_dict, [self._update(id_, data)])

    def _destroy(self, id_):
        self.service.get(id_).delete()

    # @commit
    def bulk_destroy(self, identifiers):
        for id_ in identifiers:
            self._destroy(id_)
        return identifiers

    # @commit
    def destroy(self, id_):
        self._destroy(id_)
        return id_

    def _create(self, record):
        with self.service as service:
            obj = service.create(**record)

            # Для получения id объекта - flush
            # FIXME: commit -> flush, после того, как добавится  mw:transaction
            service.session.commit()
        return obj

    # @commit
    def create(self, records):
        return map(to_dict, [self._create(record) for record in records])