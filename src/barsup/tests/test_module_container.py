# coding: utf-8

from barsup.core import init, ModuleContainer, iter_apis
from barsup.controller import Controller


class Container(ModuleContainer):

    class LibController(Controller):

        def __init__(self, lib):
            super().__init__()
            self.lib = lib

        def call(
            self,
            *,
            f: 'str',
            x: 'int',
            y: 'int'
        ) -> r'/{f:.*}':
            return self.lib.get(f)(x, y)

    def _get_entity(self, name):
        if name == 'LIB_CONT':
            return self.LibController
        else:
            return super()._get_entity(name)


config = {
    'controller': {
        'module': {
            '__realization__': 'barsup.controller.ModuleController',
            'module': 'm'
        }
    },
    'module': {
        'm': {
            '$config': {
                'controller': {
                    'math': {
                        '__realization__': 'LIB_CONT',
                        'lib': '../libs/math'
                    }
                }
            },
            '$container_clz': Container,
            '$get_config': lambda x: x
        },
        'libs': {
            '$config': {
                'lib': {
                    '__default__': {
                        '__type__': 'singleton',
                        '__realization__': 'builtins.dict'
                    },
                    'math': {
                        '$add': lambda x, y: x + y,
                        '$mul': lambda x, y: x * y
                    }
                }
            },
            '$container_clz': Container,
            '$get_config': lambda x: x
        }
    }
}


def make_api():
    return init(config, container_clz=Container, get_config=lambda x: x)


def test_module_container():
    api = make_api()

    sub_api = api._container.get('module', 'm')
    assert sub_api.populate('/math/add', x=10, y=32) == 42
    assert sub_api.populate('/math/mul', x=10, y=32) == 320

    api.populate('/module/math/add', x=10, y=32) == 42


def test_iter_api():
    api = make_api()
    actions = [
        '/'.join(path + (ctl, action))
        for (path, api_) in sorted(iter_apis(api))
        for (ctl, action) in api_
    ]
    assert actions == [
        'module/call',
        'm/math/call',
    ]
