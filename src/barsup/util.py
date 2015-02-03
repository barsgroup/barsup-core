# coding: utf-8
"""Набор вспомогательных конструкций."""
import os
import json
from types import GeneratorType

from yadic.util import merge


def serialize_to_json(obj):
    """
    Функция серриализации объектов.

    Передается в параметр default вызова json.dumps
    :param obj: Объект, который необходимо серриализовать в json
    :return:
    """
    if isinstance(obj, (map, set, GeneratorType)):
        return tuple(obj)
    else:
        raise TypeError('Type "{0}" not supported'.format(obj))


def load_configs(fnames, parser=json.load):
    """
    Загружает список конфигурационных файлов.

    Файлы должны быть разделены символом ";" и возвращать итоговую конфигурацию
    Последняя получается слиянием конфигураций из файлов,
    через ообновление с заменой в порядке следования имен файлов.
    """
    config = {}
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


def get_config_from_env(default_name='container.json'):
    """
    Возвращает имя файла конфигурации.

    Путь должен быть:
    - указан в переменной окружения $BUP_CONFIG
    - называться @default_name и находиться в папке $BUP_PATH
    В противном случае возбуждается исключение.
    """
    fname = os.environ.get('BUP_CONFIG', None)
    folder = os.environ.get('BUP_PATH', None)
    config = fname or folder and os.path.join(folder, default_name)
    if config is None:
        raise RuntimeError('BUP_PATH either BUP_CONFIG must be configured!')
    else:
        return os.path.expandvars(config)
