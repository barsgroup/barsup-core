# coding: utf-8

from sqlalchemy.inspection import inspect
from sqlalchemy.orm.properties import ColumnProperty


class _LogicException(Exception):
    @property
    def values(self):
        return {
            'msg': str(self)
        }


class BadRequest(_LogicException):
    pass


class ValidationError(BadRequest):
    pass


class NameValidationError(ValidationError):
    """
    Задано неправильное имя поля в модели
    """

    def __init__(self, field_name, model):
        self.field_name = field_name
        self.model = model

    @property
    def values(self):
        return {
            'field': self.field_name,
            'model': inspect(self.model).mapped_table.name,
            'msg': str(self)
        }

    def __str__(self):
        return (
            'Field "{0}" not found in model "{1}". '
            'Available fields: "{2}"'.format(
                self.field_name,
                inspect(self.model).mapped_table.name,
                ', '.join(col.key for col in inspect(self.model).attrs
                          if isinstance(col, ColumnProperty))
            ))


class ValueValidationError(ValidationError):
    pass


class TypeValidationError(ValueValidationError):
    def __init__(self, field, value):
        self.field_name = field.key
        self.type_name = field.type.python_type
        self.model_name = field.parent.mapped_table.name
        self.value = value

    @property
    def values(self):
        return {
            'field': self.field_name,
            'type': self.type_name,
            'value': self.value,
            'model': self.model_name,
            'msg': str(self)
        }

    def __str__(self):
        return (
            'Value "{2}" for field "{0}" from model "{3}"'
            ' can\'t be converted to "{1}"'.format(
                self.field_name, self.type_name, self.value, self.model_name))


class NullValidationError(ValueValidationError):
    def __init__(self, field):
        self.field_name = field.key
        self.model_name = field.parent.mapped_table.name

    @property
    def values(self):
        return {
            'field': self.field_name,
            'model': self.model_name,
            'msg': str(self)
        }

    def __str__(self):
        return 'Field "{0}" from model "{1}" can\'t be null'.format(
            self.field_name, self.model_name)


class LengthValidationError(ValueValidationError):
    def __init__(self, field, value):
        self.field_name = field.key
        self.field_length = field.type.length
        self.model_name = field.parent.mapped_table.name
        self.value = value
        self.value_length = len(value)

    @property
    def values(self):
        return {
            'field': self.field_name,
            'field_length': self.field_length,
            'value': self.value,
            'value_length': self.value_length,
            'model': self.model_name,
            'msg': str(self)
        }

    def __str__(self):
        return ('Value "{2}" for field "{0}" '
                'from model "{4}" must be length "{1}", '
                'but has "{3}"').format(
            self.field_name,
            self.
            field_length,
            self.value,
            self.value_length,
            self.model_name
        )


class AdapterException(ValidationError):
    def __init__(self, value, from_names, sep):
        self.value = value
        self.from_names = from_names
        self.sep = sep

    @property
    def values(self):
        return {
            'value': self.value,
            'from_names': self.from_names,
            'sep': self.sep,
            'msg': str(self)
        }

    def __str__(self):
        return 'Wrong matching value "{0}" to {1} with "{2}"'.format(
            self.value, self.from_names, self.sep
        )


class Unauthorized(_LogicException):
    def __str__(self):
        return "User is not logged"


class Forbidden(_LogicException):
    def __init__(self, uid, controller, action):
        self.uid = uid
        self.controller = controller
        self.action = action

    @property
    def values(self):
        return {
            'uid': self.uid,
            'controller': self.controller,
            'action': self.action
        }

    def __str__(self):
        return 'User "{0}" access denied for "{1}/{2}"'.format(
            self.uid, self.controller, self.action
        )


class NotFound(_LogicException):
    def __str__(self):
        return "Record not found"
