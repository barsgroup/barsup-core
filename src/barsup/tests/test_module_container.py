# coding: utf-8

from barsup.core import init, ModuleContainer, iter_frontends
from barsup.controller import Controller


class Container(ModuleContainer):

    class MathController(Controller):

        def __init__(self, lib):
            super().__init__()
            self.lib = lib

        def call(self, *, f, x, y):
            return self.lib.get(f)(x, y)

    def _get_entity(self, name):
        if name == 'MathController':
            return self.MathController
        else:
            return super()._get_entity(name)

root_spec = {
    'paths': {
        '/module{subroute}': {
            'get': {
                'operationId': 'module.call',
                'parameters': [
                    {
                        'name': 'subroute',
                        'type': 'string',
                        'in': 'path'
                    }
                ]
            }
        }
    }
}

module_spec = {
    'paths': {
        '/math/{f}': {
            'get': {
                'operationId': 'MathController.call',
                'parameters': [
                    {'name': 'f', 'in': 'path', 'type': 'string'},
                    {'name': 'x', 'in': 'query', 'type': 'integer'},
                    {'name': 'y', 'in': 'query', 'type': 'integer'},
                ]
            }
        }
    }
}

config = {
    'frontend': {
        'default': {
            '$spec': root_spec
        }
    },
    'controller': {
        'module': {
            '__realization__': 'barsup.controller.ModuleController',
            'module': 'm'
        }
    },
    'module': {
        'm': {
            '$config': {
                'frontend': {
                    'default': {
                        '$spec': module_spec
                    }
                },
                'controller': {
                    'MathController': {
                        '__realization__': 'MathController',
                        'lib': '../libs/math'
                    }
                }
            },
            '$container_clz': Container,
            '$get_config': lambda x: x
        },
        'libs': {
            '$config': {
                'frontend': {
                    'default': {
                        '$spec': {}
                    }
                },
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
    assert sub_api.populate('GET', '/math/add', x=10, y=32) == 42
    assert sub_api.populate('GET', '/math/mul', x=10, y=32) == 320

    api.populate('GET', '/module/math/add', x=10, y=32) == 42


def test_iter_api():
    api = make_api()
    actions = [
        '/'.join(path + (ctl, action))
        for (path, fend) in sorted(iter_frontends(api))
        for (ctl, action) in fend.api
    ]
    assert actions == [
        'module/call',
        'm/MathController/call',
    ]
