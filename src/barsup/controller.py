# coding: utf-8

from yadic.container import Injectable


class Controller:
    """
    Прототип контроллера
    """

    class _ActionsSet:
        """
        Итератор actions, предоставляющий для
        каждого действия декларацию его параметров
        """

        def __get__(self, instance, owner):
            assert instance is None, "\"actions\" is a class-descriptor!"
            for attr_name in dir(owner):
                if not attr_name.startswith('_'):
                    attr = getattr(owner, attr_name)
                    if callable(attr) and getattr(
                        attr, '__annotations__', None
                    ):
                        decl = attr.__annotations__.copy()
                        yield decl.pop('return'), attr.__name__, decl

    actions = _ActionsSet()


class DictController(Controller, metaclass=Injectable):
    """
    Представляет уровень контроллера

    Инжектирует в себя:
        - service - компонент, отвечающий за уровень сервиса

    Выполняет задачи:
        - Декларация и проверка на тип входящих параметров
        - ...

    """

    depends_on = ('service',)
    __slots__ = depends_on

    # --- actions ---

    def read(
        self,
        start: 'int'=None,
        limit: 'int'=None,
        page: 'int'=None,
        query: 'str'=None,
        filter: 'json'=None,
        group: 'str'=None,
        sort: 'json'=None
    ) -> r'/read':
        return self.service().filters(
            filter or []
        ).sorts(
            sort or []
        ).limiter(
            start, limit
        ).read()

    def get(
        self,
        id_: "int",
        filter: "json"=None
    ) -> r"/read/{id_:\d+}":
        return self.service.filter_by_id(id_).filters(filter or []).get()

    def bulk_update(
        self,
        records: "list"
    ) -> r"/update":
        return [self._update(record.pop('id'), record)
                for record in records]

    def update(
        self,
        id_: "int",
        data: "dict"
    ) -> r"/update/{id_:\d+}":
        return self._update(id_, data)

    def bulk_destroy(
        self,
        identifiers: "list"
    ) -> r"/destroy/":
        for id_ in identifiers:
            self._destroy(id_)
        return identifiers

    def destroy(
        self,
        id_: "int"
    ) -> "/destroy/{id_:\d+}":
        self._destroy(id_)
        return id_

    def create(
        self,
        data: "dict"
    ) -> r"/create":
        return self.service.create(**data)

    def bulk_create(
        self,
        records: "list"
    ) -> r"/bulk-create":
        return (self._create(data) for data in records)

    # --- internals ---

    def _update(self, id_, record):
        return self.service.filter_by_id(id_).update(**record)

    def _destroy(self, id_):
        self.service.filter_by_id(id_).delete()


__all__ = (DictController, Controller)
