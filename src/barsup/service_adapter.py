# coding: utf-8

import barsup.exceptions as exc


class Splitter:
    def __init__(self, name, names, sep=' '):
        self._name = name
        self._names = names
        self._sep = sep

    def to_record(self, result, params):
        if params.get(self._name):
            value = params[self._name]
            values = value.split(self._sep)
            if len(self._names) != len(values):
                raise exc.ValueValidationError('Wrong matching value "{0}" to {1} with "{2}"'.format(
                    value, self._names, self._sep
                ))
            result.update(dict(zip(self._names, values)))
        return result, params

    def from_record(self, result, params):
        value = self._sep.join([params[name] for name in self._names])
        result[self._name] = value
        return result, params


class DefaultAdapter:
    def __init__(self, model, include, exclude):
        self._include = include
        self._exclude = exclude

        self._model = model

    def to_record(self, result, params):
        res = {}
        for k, v in params.items():
            if not hasattr(self._model, k):
                if k not in self._include:  # Обработали адаптеры
                    raise exc.NameValidationError('Name {0} not found in model'.format(k))
            else:
                res[k] = v

        res = self.include_exclude(res)
        result.update(res)
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


ADAPTERS = {
    'Splitter': Splitter,
    'default': DefaultAdapter
}

