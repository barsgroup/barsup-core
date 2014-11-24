# coding: utf-8
from datetime import date


def to_dict(obj, excludes=frozenset(['metadata',
                                     'classes',
                                     'prepare'])):
    """
    Серриализация sqlalchemy-объектов в dict

    :param obj: Объект sqlalchemy
    :param excludes: Исключения
    :return: dict
    """
    fields = {}
    for field in dir(obj):
        # алхимия генерирует вложенные коллекции с таким постфиксом
        if field.startswith('_') or field in excludes or u'_collection' in field:
            continue

        value = obj.__getattribute__(field)
        if callable(value):
            continue

        # Если value - соединеннная json-ом модель
        elif hasattr(value, '_sa_class_manager'):
            value = to_dict(value)

        elif isinstance(value, date):
            # value = time.mktime(value.timetuple()) * 1000
            value = date.strftime(value, '%m/%d/%Y')

        assert value is None or isinstance(value, (
            str, unicode, list, tuple, dict, int, float
        )), "Unserializable value: %r :: %s!" % (value, type(value))
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
