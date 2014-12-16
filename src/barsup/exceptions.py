# coding: utf-8


class LogicException(Exception):
    pass


class Unauthorized(LogicException):
    pass


class BadRequest(LogicException):
    pass


class Forbidden(LogicException):
    pass


class NotFound(LogicException):
    pass