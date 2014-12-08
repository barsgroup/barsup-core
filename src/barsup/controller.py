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

    def read(self,
             start: 'int'=None,
             limit: 'int'=None,
             page: 'int'=None,
             query: 'str'=None,
             filter: 'json'=None,
             group: 'str'=None,
             sort: 'json'=None) -> r'/read':
        return map(to_dict,
                   self.service().filters(
                       filter or []
                   ).sorts(
                       sort or []
                   ).limiter(start, limit
                   ).read()
        )

    def get(self, id_: "int", filter: "json"=None) -> r"/read/{id_:\d+}":
        return to_dict(
            self.service.filter_by_id(id_).filters(filter or []).get()
        )

    def _update(self, id_, record):
        return self.service.filter_by_id(id_).update(**record)

    def bulk_update(self, records: "list") -> r"/update":
        return map(to_dict,
                   [self._update(record['id'], record) for record in records])

    def update(self, id_: "int", data: "dict") -> r"/update/{id_:\d+}":
        return map(to_dict, [self._update(id_, data)])

    def _destroy(self, id_):
        self.service.filter_by_id(id_).delete()

    def bulk_destroy(self, identifiers: "list") -> r"/destroy/":
        for id_ in identifiers:
            self._destroy(id_)
        return identifiers

    def destroy(self, id_: "int") -> "/destroy/{id_:\d+}":
        self._destroy(id_)
        return id_

    def _create(self, record):
        return self.service.create(**record)

    def create(self, records: "list") -> r"/create":
        return map(to_dict, (self._create(record) for record in records))


__all__ = (DictController,)
