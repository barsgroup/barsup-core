# coding: utf-8

import tempfile
import json

from barsup.util import load_configs


def _write_dump(data, fobj):
    raw = json.dumps(data)
    try:
        fobj.write(bytes(raw, 'UTF-8'))  # py3.x
    except TypeError:
        fobj.write(raw)  # py2.x
    fobj.flush()


def test_config_loader():
    """
    Тестирует загрузку с обновлением файлов конфигурации
    """
    with tempfile.NamedTemporaryFile() as f1:
        _write_dump(
            {
                'group': {
                    'elem1': {
                        'a': 1,
                        'b': 2,
                        'dic': {
                            'x': 100
                        }
                    }
                }
            },
            f1
        )

        with tempfile.NamedTemporaryFile() as f2:
            _write_dump(
                {
                    'group': {
                        'elem1': {
                            'a': 2,
                            'c': 2,
                            'dic': {
                                'y': 200
                            }
                        },
                        'elem2': {
                            'key': 'val'
                        }
                    }
                },
                f2
            )

            assert load_configs(';'.join((f1.name, f2.name))) == {
                'group': {
                    'elem1': {
                        'a': 2,
                        'b': 2,
                        'c': 2,
                        'dic': {
                            'y': 200
                        }
                    },
                    'elem2': {
                        'key': 'val'
                    }
                }
            }
