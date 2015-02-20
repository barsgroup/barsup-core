# coding: utf-8
"""Вспомогательные конструкции для тестов CLI."""
from barsup.controller import Controller


class CLIController(Controller):

    """Заглушка тестового контроллера для CLI."""

    def read(self, params) -> ('GET', r'/read'):
        """
        Возвращает полученные параметры.

        :param params:
        :return:
        """
        return params

    def write(self, params) -> ('GET', r'/write'):
        """
        Возвращает полученные параметры.

        :param params:
        :return:
        """
        return params
