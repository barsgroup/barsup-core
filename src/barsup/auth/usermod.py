# coding: utf-8
"""Скрипт создания пользователя и роли."""

import sys
import argparse


_NOT_IMPLEMENTED = False, "Not implemented!"


parser = argparse.ArgumentParser(description="Manages users, roles e.t.c")
parser.add_argument(
    'entity', type=str, choices=['user', 'role'],
    help='entity to modify')
parser.add_argument(
    'action', type=str, choices=['create', 'delete', 'update'],
    help='what to do')


def _role_create(container):
    return _NOT_IMPLEMENTED


def _role_update(container):
    return _NOT_IMPLEMENTED


def _role_delete(container):
    return _NOT_IMPLEMENTED


def _user_create(container):
    return _NOT_IMPLEMENTED


def _user_update(container):
    return _NOT_IMPLEMENTED


def _user_delete(container):
    return _NOT_IMPLEMENTED


if __name__ == '__main__':
    from barsup.core import init
    from barsup.util import get_config_from_env
    try:
        conf_file = get_config_from_env()
    except RuntimeError as e:
        print('Error:', e)
        sys.exit(1)

    cfg, args = parser.parse_known_args()
    action = globals()['_{cfg.entity}_{cfg.action}'.format(cfg=cfg)]

    api = init(conf_file)
    ok, message = action(api._container)
    print(message)
    sys.exit(1 if not ok else 0)
