# coding: utf-8
import json
import os

from barsup.cli import APICLI


class TestableCLI(APICLI):

    def __init__(self, buf, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._out = buf.append


def make_cli(buf):
    path_test = os.path.join(os.path.dirname(__file__), 'container.json')
    return TestableCLI(buf, path_test)


def test_simple_cli():
    """Проверяет, вызывается ли экшн корректно."""

    buf = []
    assert make_cli(buf).run(
        ['SimpleController', 'read', "{'params': {'a':1}}"]
    ) == TestableCLI.EXIT_OK
    assert len(buf) == 1
    result = json.loads(buf[0])
    assert isinstance(result, dict)
    assert result['a'] == 1


def test_wrong_action():
    """Проверяет вывод ошибки при несуществующем controller/action."""

    make_cli([]).run(['SimpleController', 'get', ]) == TestableCLI.EXIT_ERROR


def test_hierarchy():
    """Проверяет построение иерархии controllers/actions."""

    result = make_cli([]).hierarchy
    assert isinstance(result, dict)
    assert 'SimpleController' in result
    assert 'write' in result['SimpleController']
    assert 'read' in result['SimpleController']
    assert 'get' not in result['SimpleController']
