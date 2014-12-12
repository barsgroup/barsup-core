# coding: utf-8
from datetime import date
from sqlalchemy.util._collections import KeyedTuple


def to_dict(obj, excludes=frozenset(['metadata',
                                     'classes',
                                     'prepare'])):
    """
    Серриализация sqlalchemy-объектов в dict

    :param obj: Объект sqlalchemy
    :param excludes: Исключения
    :return: dict
    """
    if isinstance(obj, KeyedTuple):
        return obj._asdict()

    fields = {}
    for field in dir(obj):
        # алхимия генерирует вложенные коллекции с таким постфиксом
        if field.startswith('_') or (
                        field in excludes or '_collection' in field):
            continue

        value = obj.__getattribute__(field)
        if callable(value):
            continue

        # Если value - соединеннная json-ом модель
        elif hasattr(value, '_sa_class_manager'):
            value = to_dict(value)

        elif isinstance(value, date):
            value = date.strftime(value, '%m/%d/%Y')

        assert value is None or isinstance(value, (
            str, list, tuple, dict, int, float
        )), "Unserializable value: %r :: %s!" % (value, type(value))

        # Преобразование в плоские списки значений
        # {'user': {'id': 1, 'name': 'Иванов'} ->
        # {'user.id': 1, 'user.name': 'Иванов'}
        if isinstance(value, dict):
            for child_field, child_value in value.items():
                complex_field = '{0}.{1}'.format(field, child_field)
                fields[complex_field] = child_value
        else:
            fields[field] = value

    return fields


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
        return date.fromtimestamp(float(value))
    return value
