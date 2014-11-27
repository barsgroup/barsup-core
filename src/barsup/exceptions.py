# coding: utf-8


class NeedLogin(Exception):
    def __init__(self):
        self.status = 'need_login'


class ValidationError(Exception):
    pass
