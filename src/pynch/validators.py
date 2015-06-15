# coding: utf-8
"""Валидаторы"""
import json

from pynch import exceptions as exc


__all__ = ('VALIDATORS',)


class Validator:
    """В том числе приведение к типу"""

    def __init__(self, *, name, required=False, format=None, **kwargs):
        self.name = name
        self.required = required
        self.format = format

    def __call__(self, in_dict, out_dict):
        try:
            raw_value = in_dict.pop(self.name)
        except KeyError:
            if self.required:
                raise exc.ValidationError(
                    'Parameter "%s" is required!' % self.name)
        else:
            try:
                value = self.validate(raw_value)
            except (KeyError, ValueError, TypeError) as e:
                raise exc.ValidationError(
                    'Value of parameter "%s" is incorrect!' % self.name
                ) from e
            else:
                assert self.name not in out_dict
                out_dict[self.name] = value

    @staticmethod
    def validate(value):
        raise NotImplementedError()


class IntegerValidator(Validator):
    validate = staticmethod(int)


class FloatValidator(Validator):
    validate = staticmethod(float)


class StringValidator(Validator):
    validate = staticmethod(str)


class ObjectValidator(Validator):
    validate = staticmethod(json.loads)


class AsIsValidator(Validator):
    # объект ранее преобразовывается в json
    validate = staticmethod(lambda x: x)


VALIDATORS = {
    'integer': {
        'default': IntegerValidator
    },
    'string': {
        'default': StringValidator,
        'as-is': AsIsValidator,
        'json': ObjectValidator,
        'date': None,
        'date-time': None
    },
    'float': {
        'default': FloatValidator
    },
}
