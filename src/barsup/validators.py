# coding: utf-8

import json


__all__ = ('VALIDATORS', 'ValidationError')


class ValidationError(ValueError):
    pass


class Validator:

    def __init__(self, *, name, required=False, **kwargs):
        self.name = name
        self.required = required

    def __call__(self, in_dict, out_dict):
        try:
            raw_value = in_dict.pop(self.name)
        except KeyError:
            if self.required:
                raise ValidationError(
                    'Parameter "%s" is required!' % self.name)
        else:
            try:
                value = self.validate(raw_value)
            except (KeyError, ValueError, TypeError) as e:
                raise ValidationError(
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


VALIDATORS = {
    'integer': IntegerValidator,
    'string': StringValidator,
    'float': FloatValidator,
}
