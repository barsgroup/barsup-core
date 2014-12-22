# coding: utf-8

AVAILABLE_ACTIONS = []


def list_actions(cont, api):
    """
    initware, получающее список экшнов для подсистемы проверки прав
    """
    AVAILABLE_ACTIONS.extend(api)
