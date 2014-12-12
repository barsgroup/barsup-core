# coding: utf-8
from types import GeneratorType


def serialize_to_json(obj):
    if isinstance(obj, (map, set, GeneratorType)):
        return tuple(obj)
    else:
        raise TypeError('Type "{0}" not supported'.format(obj))