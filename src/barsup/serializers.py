# coding: utf-8
from datetime import date


def to_dict(obj, excludes=frozenset(['metadata',
                                     'classes',
                                     'individual_collection',
                                     'userbook_collection'])):
    fields = {}
    for field in dir(obj):
        if field.startswith('_') or field in excludes:
            continue
        value = obj.__getattribute__(field)
        if callable(value):
            continue

        elif hasattr(value, '_sa_class_manager'):
            value = to_dict(value)

        elif isinstance(value, date):
            value = date.strftime(value, '%d.%m.%Y')

        assert value is None or isinstance(value, (
            str, unicode, list, tuple, dict, int, float
        )), "Unserializable value: %r :: %s!" % (value, type(value))
        fields[field] = value
    return fields
