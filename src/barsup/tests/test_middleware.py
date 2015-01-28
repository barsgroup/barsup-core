# coding: utf-8

from yadic.container import Container

from barsup.core import API
from barsup.tests.test_core import FakeRouter


def inc_a(next, controller, action, **params):
    params['a'] += 1
    return next(controller, action, **params)


def inject_b(val):
    def inner(next, controller, action, **params):
        params['b'] = val
        return next(controller, action, **params)
    return inner


def replace_action_to(val):
    def inner(next, controller, action, **params):
        return next(controller, val, **params)
    return inner


def interrupt_and_return(val):
    def inner(next, controller, action, **params):
        return val
    return inner


def add_to_context(**kwargs):
    def inner(next, controller, action, *, _context, **params):
        _context.update(**kwargs)
        return next(controller, action, _context=_context, **params)
    return inner


def ensure_presense_of(**kwargs):
    def inner(next, controller, action, *, _context, **params):
        assert all(
            k in _context and _context[k] == v
            for k, v in kwargs.items()
        )
        return next(controller, action, _context=_context, **params)
    return inner


class FakeContainer(Container):

    class Controller:

        @staticmethod
        def real_action(**kwargs):
            return kwargs

    def get(self, group, name):
        assert (group, name) == ('controller', 'Controller')
        return self.Controller

    def itergroup(self, group):
        assert group == 'controller'
        return iter([])


def make_api(*middleware):
    return API(
        container=FakeContainer({}),
        router=FakeRouter,
        middleware=middleware,
        initware=[],
    )


def test_middlewares():
    api = make_api(
        inc_a,
        inject_b(42),
        replace_action_to('real_action')
    )
    assert api.call('Controller', 'action', a=1) == {'a': 2, 'b': 42}


def test_interruption_by_middleware():
    api = make_api(
        interrupt_and_return(123)
    )
    assert api.call('Controller', 'real_action') == 123


def test_middleware_context():
    api = make_api(
        add_to_context(a=1, b="B"),
        ensure_presense_of(a=1, b="B")
    )
    api.call('Controller', 'real_action')
