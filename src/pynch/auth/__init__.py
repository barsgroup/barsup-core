# coding: utf-8
"""Пакет для аутентификации/авторизации."""

AVAILABLE_ACTIONS = []


def list_actions(cont, fend):
    """initware, получающее список экшнов для подсистемы проверки прав. """
    from pynch.core import iter_frontends

    for path, sub_fend in iter_frontends(fend):
        path = '/'.join(path + ('%s',))
        for ctl, action in sub_fend.api:
            AVAILABLE_ACTIONS.append((path % ctl, action))
