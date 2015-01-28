# coding: utf-8

from barsup.core import API
from yadic.container import Container


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
        router=lambda *args, **kwargs: None,
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
    assert api.call('Container', 'real_action') == 123
