# coding: utf-8
from datetime import date
from types import GeneratorType


def serialize_to_json(obj):
    if isinstance(obj, (map, set, GeneratorType)):
        return tuple(obj)
    elif isinstance(obj, date):
        return date.strftime(obj, '%m/%d/%Y')
    else:
        raise TypeError('Type "{0}" not supported'.format(obj))