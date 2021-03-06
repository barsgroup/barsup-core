# coding: utf-8
"""Реализация CRUD-контроллеров."""

from yadic.container import Injectable


class Controller:
    """Базовая реализация."""

    pass


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
    ) -> ("GET", r"/read"):
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

    def get(self, id, filter=None):
        """
        Действие на получение одного объекта.

        :param id: Идентификатор объекта
        :param filter: Фильтр
        :return: Объект в виде словаря
        """
        return self.service.filter_by_id(id).filters(filter or []).get()

    def bulk_update(
        self,
        records: "list"
    ) -> ("POST", r"/update"):
        """
        Действие изменения списка объектов.

        :param records: Список объектов для изменения
        :return: Список измененных объектов
        """
        return [self._update(record.pop('id'), record)
                for record in records]

    def update(
        self,
        id: "int",
        data: "dict"
    ) -> ("POST", r"/update/{id_:\d+}"):
        """
        Действие изменения одного объекта.

        :param id: Идентификатор объекта
        :param data: Поля со значения для изменения
        :return: Измененный объект
        """
        return self._update(id, data)

    def bulk_destroy(
        self,
        identifiers: "list"
    ) -> ("POST", r"/destroy/"):
        """
        Действие для удаления списка объектов.

        :param identifiers: Список идентификаторов
        :return: Список удаленных идентификаторов
        """
        for id_ in identifiers:
            self._destroy(id_)
        return identifiers

    def destroy(self, id):
        """
        Действие удаление одного объекта.

        :param id_: Идентификатор объекта
        :return: Идентификатор удаленного объекта
        """
        self._destroy(id)
        return id

    def create(
        self,
        data: "dict"
    ) -> ("POST", r"/create"):
        """
        Действие создания одного объекта.

        :param data: Данные объекта
        :return: Созданный объект
        """
        return self.service.create(**data)

    def bulk_create(
        self,
        records: "list"
    ) -> ("POST", r"/bulk-create"):
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

    def __init__(self, module):
        """Инициализирует контроллер модуля.

        :param module: Frontend модуля
        :type module: pynch.core.Frontend
        """
        self._module = module

    def call(self, *, subroute, _context):
        """
        Действие делегирования внутрь API стороннего модуля.

        :param _subroute:
        :param kwargs:
        :return:
        """
        from pynch.core import Redirection

        return Redirection(self._module, subroute, _context)


__all__ = ('DictController', 'Controller', 'ModuleController')
