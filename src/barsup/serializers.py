# coding: utf-8
from datetime import date


def to_dict(obj, excludes=frozenset(['metadata',
                                     'classes',
                                     'prepare'])):
    fields = {}
    for field in dir(obj):
        if (field.startswith('_') or
                    field in excludes or
                    # алхимия генерирует вложенные коллекции с таким постфиксом
                    u'_collection' in field):
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
