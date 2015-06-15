# coding: utf-8
"""
Модуль для адаптеров.

Необходимы для преобразования значений объектов моделей в стандартные python
типы и обратно. Работает на уровне сервисов (services).
"""

import barsup.exceptions as exc


class Splitter:

    """
    Адаптер для комплексного представления полей.

    Например на уровне API может быть поле fio: "Иванов Иван Иванович",
    а на уровне моделей может быть три поля: first, last, patronymic
    """

    def __init__(self, to_name, from_names, sep=' '):
        """
        Конструктор объекта.

        :param str to_name: Поле, для преобразование
        :param list from_names:  Наименование полей, во что нужно преобразовать
        :param str sep: Разделитель для преобразования
        :return:
        """
        self._to_name = to_name
        self._from_names = from_names
        self._sep = sep

    def to_record(self, result, params):
        """
        Преобразование вида dict -> model object.

        :param dict result: Результирующий словарь объектов
        :param dict params: Входные параметры
        :return tuple: Кортеж пар (Результирующий словарь объектов,
        Входные параметры)
        """
        if params.get(self._to_name):
            value = params[self._to_name]
            values = value.split(self._sep)
            if len(self._from_names) != len(values):
                raise exc.AdapterException(value, self._from_names, self._sep)
            result.update(dict(zip(self._from_names, values)))
        return result, params

    def from_record(self, result, params):
        """
        Преобразование вида model object -> dict.

        :param dict result: Результирующий словарь объектов
        :param dict params: Входные параметры модели
        :return tuple: Кортеж пар (Результирующий словарь объектов,
        Входные параметры модели)
        """
        value = self._sep.join(params[name] for name in self._from_names)
        result[self._to_name] = value
        return result, params


class DefaultAdapter:

    """
    Умолчательный адаптер.

    Доукомплектовывает результирующий словарь словарем параметров
    """

    def __init__(self, model, include, exclude):
        """
        Конструктор объекта.

        :param dict model: Модель
        :param list include: Список полей для обязательного включения
        :param list exclude: Список полей для исключения
        :return:
        """
        self._include = include or []
        self._exclude = exclude or []
        self._model = model

    def to_record(self, result, params):
        """
        Преобразование вида dict -> model object.

        :param dict result: Результирующий словарь объектов
        :param dict params: Входные параметры
        :return tuple: Кортеж пар (Результирующий словарь объектов,
        Входные параметры)
        """
        res = {}
        for k, v in params.items():
            if not hasattr(self._model, k):
                if k not in self._include:  # Обработали адаптеры
                    raise exc.NameValidationError(k, self._model)
            else:
                res[k] = v

        result.update(self.include_exclude(res))
        return result, params

    def from_record(self, result, params):
        """
        Преобразование вида model object -> dict.

        :param dict result: Результирующий словарь объектов
        :param dict params: Входные параметры модели
        :return tuple: Кортеж пар (Результирующий словарь объектов,
        Входные параметры модели)
        """
        res = self.include_exclude(params)
        result.update(res)
        return result, params

    def include_exclude(self, params):
        """
        Включает/исключает поля из результат.

        :param dict params: Входной словарь параметров
        :return dict: Результирующий словарь
        """
        if self._include:
            return {k: v for k, v in params.items() if k in self._include}
        elif self._exclude:
            return {k: v for k, v in params.items() if k not in self._exclude}
        return params
