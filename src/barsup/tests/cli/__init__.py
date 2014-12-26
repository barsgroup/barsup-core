# coding: utf-8
from barsup.controller import Controller


class CLIController(Controller):

    def read(self, params) -> '/read':
        return params

    def write(self, params) -> '/write':
        return params
