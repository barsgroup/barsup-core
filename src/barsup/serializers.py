# coding: utf-8
from datetime import date


def convert(mapping_item, value):
    """
    Преобразование входящих значений согласно типам колонок

    :param mapping_item: Наименование поля
    :param value: Значение поля
    :return: Преобразованное значение
    """
    type_ = mapping_item.type
    if issubclass(type_.python_type, date):
        if len(str(value)) == 13:  # timestamp c милисекундами
            value /= 1000.0
        value = date.fromtimestamp(float(value))
    return value
