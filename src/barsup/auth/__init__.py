# coding: utf-8
"""Пакет для аутентификации/авторизации."""

AVAILABLE_ACTIONS = []


def list_actions(cont, api):
    """initware, получающее список экшнов для подсистемы проверки прав. """
    from barsup.core import iter_apis

    for path, sub_api in iter_apis(api):
        path = '/'.join(path + ('%s',))
        for ctl, action in sub_api:
            AVAILABLE_ACTIONS.append((path % ctl, action))
