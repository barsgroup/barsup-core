# coding: utf-8
import json
import os
import builtins

import pytest

from barsup.cli import CLI


def wrap_print(print_function):
    def inner(f):
        def wrapper():
            print = builtins.print
            builtins.print = print_function
            f()
            builtins.print = print

        return wrapper

    return inner


def simple_cli(*args, sep=' ', end='\n', file=None):
    result = json.loads(args[0])
    assert isinstance(result, dict)
    assert result['a'] == 1


@wrap_print(simple_cli)
def test_simple_cli():
    """
    Обычное тестирование вызова контроллера и экшена
    """

    path_test = os.environ.get('BUP_TESTS')
    cli = CLI(os.path.join(path_test, 'cli', 'container.json'))
    cli.run(['SimpleController', 'read', "{'params': {'a':1}}"])


def test_cli_without_file():
    """
    Если не передали путь до файла конфигурации:
    завершение работы со статусом 1
    """
    with pytest.raises(SystemExit):
        cli = CLI(None)
        cli.run(['SimpleController', 'read', ])


def test_wrong_action():
    """
    Несуществующий контроллер
    """
    path_test = os.environ.get('BUP_TESTS')
    cli = CLI(os.path.join(path_test, 'cli', 'container.json'))
    with pytest.raises(ValueError):
        cli.run(['SimpleController', 'get', ])


def test_hierarchy():
    path_test = os.environ.get('BUP_TESTS')
    cli = CLI(os.path.join(path_test, 'cli', 'container.json'))

    result = cli.hierarchy
    assert isinstance(result, dict)
    assert 'SimpleController' in result
    assert 'write' in result['SimpleController']
    assert 'read' in result['SimpleController']
    assert 'get' not in result['SimpleController']


def without_args(*args, sep=' ', end='\n', file=None):
    assert args[0] == ''


@wrap_print(without_args)
def test_without_args():
    path_test = os.environ.get('BUP_TESTS')
    cli = CLI(os.path.join(path_test, 'cli', 'container.json'))
    cli.run(args=[])


def complete_actions(*args, sep=' ', end='\n', file=None):
    assert args[0] in ('read', 'write')


@wrap_print(complete_actions)
def test_complete_actions():
    os.environ['COMP_LINE'] = 'cli SimpleController read'
    path_test = os.environ.get('BUP_TESTS')
    cli = CLI(os.path.join(path_test, 'cli', 'container.json'))
    cli.run(args=['--complete', 'SimpleController', ''])
