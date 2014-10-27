# coding: utf-8
from barsup.serializers import to_dict
from barsup.container import Injectable


class Service(object):
    __metaclass__ = Injectable

    serialize = staticmethod(to_dict)
    depends_on = ('model', 'session', 'db_mapper')

    def query(self, *args):
        if '*' in args:
            self._queryset = self.session.get().query(self.model)
        else:
            self._queryset = self.session.get().query(
                *map(lambda x: getattr(self.model, x), args)
            )

    def filter(self, **kwargs):
        self._queryset = self._queryset.filter(
            *(getattr(self.model, param) == value
              for param, value in kwargs.items())
        )

    def grouper(self, *args):
        self._queryset = self._queryset.group_by(*args)

    def sorter(self, **kwargs):
        self._queryset = self._queryset.order_by(**kwargs)

    def _load(self):
        return self._queryset.all()

    def load(self):
        return map(self.serialize, self._load())

    def limiter(self, offset, limit):
        self._queryset = self._queryset.limit(limit).offset(offset)

    # Record methods
    def create(self, **kwargs):
        instance = self._init(self.model(), **kwargs)
        self.session.get().add(instance)
        return instance

    def read(self):
        return self._queryset[0]

    def update(self, obj, **kwargs):
        for item, value in kwargs.items():
            assert hasattr(obj, item)
            setattr(obj, item, value)

        self.session.get().add(obj)

    def delete(self, obj):
        self.session.get().delete(obj)

    def _init(self, obj, **kwargs):
        for item, value in kwargs.items():
            assert hasattr(obj, item)
            setattr(obj, item, value)
        return obj
