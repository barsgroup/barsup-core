# coding: utf-8


def to_dict(obj, excludes=frozenset(['metadata',
                                     'classes',
                                     'individual_collection'])):
    fields = {}
    for field in dir(obj):
        if field.startswith('_') or field in excludes:
            continue
        value = obj.__getattribute__(field)
        if callable(value):
            continue

        if hasattr(value, '_sa_class_manager'):
            value = to_dict(value)

        assert value is None or isinstance(value, (
            str, unicode, list, tuple, dict, int, float
        )), "Unserializable value: %r :: %s!" % (value, type(value))
        fields[field] = value
    return fields
