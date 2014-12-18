# coding: utf-8


class _LogicException(Exception):
    pass


class BadRequest(_LogicException):
    pass


class ValidationError(BadRequest):
    pass


class NameValidationError(ValidationError):
    pass


class ValueValidationError(ValidationError):
    pass


class TypeValidationError(ValueValidationError):
    pass


class NullValidationError(ValueValidationError):
    pass


class LengthValidationError(ValueValidationError):
    pass


class Unauthorized(_LogicException):
    pass


class Forbidden(_LogicException):
    pass


class NotFound(_LogicException):
    pass