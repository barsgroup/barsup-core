# coding: utf-8

import barsup.exceptions as exc


class Splitter:
    def __init__(self, to_name, from_names, sep=' '):
        self._to_name = to_name
        self._from_names = from_names
        self._sep = sep

    def to_record(self, result, params):
        if params.get(self._to_name):
            value = params[self._to_name]
            values = value.split(self._sep)
            if len(self._from_names) != len(values):
                raise exc.ValueValidationError(
                    'Wrong matching value "{0}" to {1} with "{2}"'.format(
                        value, self._from_names, self._sep
                    ))
            result.update(dict(zip(self._from_names, values)))
        return result, params

    def from_record(self, result, params):
        value = self._sep.join(params[name] for name in self._from_names)
        result[self._to_name] = value
        return result, params


class DefaultAdapter:
    def __init__(self, model, include, exclude):
        self._include = include or []
        self._exclude = exclude or []

        self._model = model

    def to_record(self, result, params):
        res = {}
        for k, v in params.items():
            if not hasattr(self._model, k):
                if k not in self._include:  # Обработали адаптеры
                    raise exc.NameValidationError(
                        'Name {0} not found in model'.format(k))
            else:
                res[k] = v

        result.update(self.include_exclude(res))
        return result, params

    def from_record(self, result, params):
        res = self.include_exclude(params)
        result.update(res)
        return result, params

    def include_exclude(self, params):
        if self._include:
            return {k: v for k, v in params.items() if k in self._include}
        elif self._exclude:
            return {k: v for k, v in params.items() if k not in self._exclude}
        return params