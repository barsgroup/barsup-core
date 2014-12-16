# coding: utf-8


class _LogicException(Exception):
    pass


class BadRequest(_LogicException):
    pass


class Unauthorized(_LogicException):
    pass


class Forbidden(_LogicException):
    pass


class NotFound(_LogicException):
    pass