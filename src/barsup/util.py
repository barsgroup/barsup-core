# coding: utf-8
import os
import json
from types import GeneratorType

from yadic.util import merge


def serialize_to_json(obj):
    if isinstance(obj, (map, set, GeneratorType)):
        return tuple(obj)
    else:
        raise TypeError('Type "{0}" not supported'.format(obj))


def load_configs(fnames, parser=json.load):
    """
    Загружает список конфигурационных файлов,
    разделённых символом ";" и возвращает итоговую конфигурацию.
    Последняя получается слиянием конфигураций из файлов,
    через ообновление с заменой в порядке следования имен файлов.
    """
    config = {}
    if isinstance(fnames, dict):
        config = fnames
    else:
        for fname in os.path.expandvars(fnames).split(';'):
            with open(os.path.expandvars(fname)) as f:
                patch = parser(f)
                config = merge(
                    config, patch,
                    # словари сливаются вплоть до второго уровня вложенности
                    # те же, что расположены глубже, заменяются старый новым
                    lambda v1, v2, m, path: (
                        merge(v1, v2, m, path)
                        if (
                            isinstance(v1, dict) and isinstance(v2, dict)
                            and
                            len(path) <= 2
                        ) else
                        v2
                    )
                )
    return config
