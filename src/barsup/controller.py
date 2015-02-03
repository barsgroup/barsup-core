# coding: utf-8
"""Реализация CRUD-контроллеров."""

from yadic.container import Injectable


class Controller:

    """Базовая реализация."""

    class _ActionsSet:

        """
        Итератор actions.

        Предоставляюет для каждого действия декларацию его параметров
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
    Представляет уровень CRUD-контроллера.

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
        """
        Действие для получения списка объектов.

        :param start: Начальная позиция
        :param limit: Количество записей от начальной позиции
        :param page: Номер страницы (по-умолчанию не используется)
        :param query: Поиск
        :param filter: Фильтр
        :param group: Группировка
        :param sort: Сортировка
        :return: Итератор объектов
        """
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
        """
        Действие на получение одного объекта.

        :param id_: Идентификатор объекта
        :param filter: Фильтр
        :return: Объект в виде словаря
        """
        return self.service.filter_by_id(id_).filters(filter or []).get()

    def bulk_update(
        self,
        records: "list"
    ) -> r"/update":
        """
        Действие изменения списка объектов.

        :param records: Список объектов для изменения
        :return: Список измененных объектов
        """
        return [self._update(record.pop('id'), record)
                for record in records]

    def update(
        self,
        id_: "int",
        data: "dict"
    ) -> r"/update/{id_:\d+}":
        """
        Действие изменения одного объекта.

        :param id_: Идентификатор объекта
        :param data: Поля со значения для изменения
        :return: Измененный объект
        """
        return self._update(id_, data)

    def bulk_destroy(
        self,
        identifiers: "list"
    ) -> r"/destroy/":
        """
        Действие для удаления списка объектов.

        :param identifiers: Список идентификаторов
        :return: Список удаленных идентификаторов
        """
        for id_ in identifiers:
            self._destroy(id_)
        return identifiers

    def destroy(
        self,
        id_: "int"
    ) -> "/destroy/{id_:\d+}":
        """
        Действие удаление одного объекта.

        :param id_: Идентификатор объекта
        :return: Идентификатор удаленного объекта
        """
        self._destroy(id_)
        return id_

    def create(
        self,
        data: "dict"
    ) -> r"/create":
        """
        Действие создания одного объекта.

        :param data: Данные объекта
        :return: Созданный объект
        """
        return self.service.create(**data)

    def bulk_create(
        self,
        records: "list"
    ) -> r"/bulk-create":
        """
        Действие создания списка объектов.

        :param records: Список данных об объектах
        :return: Список созданных объектов
        """
        return (self._create(data) for data in records)

    # --- internals ---

    def _update(self, id_, record):
        return self.service.filter_by_id(id_).update(**record)

    def _destroy(self, id_):
        self.service.filter_by_id(id_).delete()


class ModuleController:

    """Контроллер, делигирующий вызов внутрь стороннего модуля."""

    from barsup.router import CATCH_ALL_PARAMS

    actions = (('{_subroute:.*}', 'call', CATCH_ALL_PARAMS),)

    def __init__(self, module):
        """.

        :param module: Наименование модуля
        :return:
        """
        self._module = module

    def call(self, *, _subroute, **kwargs):
        """
        Действие делегирования внутрь API стороннего модуля.

        :param _subroute:
        :param kwargs:
        :return:
        """
        return self._module.populate(_subroute, **kwargs)


__all__ = ('DictController', 'Controller', 'ModuleController')
