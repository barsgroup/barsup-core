# coding: utf-8

from pynch.core import init, ModuleContainer
from pynch.tests.test_middleware import (
    ensure_presense_of,
    add_to_context
)


class Container(ModuleContainer):

    class Controller:

        @staticmethod
        def run():
            return True

    def _get_entity(self, name):
        if name == 'Controller':
            return self.Controller
        elif name == 'add_to_context':
            return add_to_context
        elif name == 'ensure_presense_of':
            return ensure_presense_of
        else:
            return super()._get_entity(name)


def test_context_bypass():

    api = init(
        config={
            'controller': {
                'inner': {
                    '__realization__': 'pynch.controller.ModuleController',
                    'module': 'inner'
                }
            },
            'frontend': {
                'default': {
                    '$spec': {
                        'paths': {
                            '/inner{subroute}': {
                                'get': {
                                    'operationId': 'inner.call',
                                    'parameters': [
                                        {'name': 'subroute', 'type': 'string',
                                         'in': 'path'}
                                    ]
                                }
                            }
                        }
                    }
                }
            },
            'api': {
                'default': {
                    'middleware': [
                        'add_to_context'
                    ]
                }
            },
            'middleware': {
                'add_to_context': {
                    '__type__': 'singleton',
                    '__realization__': 'add_to_context',
                    '$a': 10,
                    '$b': 'B'
                }
            },
            'module': {
                'inner': {
                    '$config': {
                        'controller': {
                            'cont': {
                                '__realization__': 'Controller',
                                '__type__': 'static'
                            }
                        },
                        'frontend': {
                            'default': {
                                '$spec': {
                                    'paths': {
                                        '/cont/run': {
                                            'get': {
                                                'operationId': 'cont.run'
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        'api': {
                            'default': {
                                'middleware': [
                                    'ensure_presense_of'
                                ]
                            }
                        },
                        'middleware': {
                            'ensure_presense_of': {
                                '__realization__': 'ensure_presense_of',
                                '__type__': 'singleton',
                                '$a': 10,
                                '$b': 'B'
                            }
                        }
                    },
                    '$get_config': lambda x: x,
                    '$container_clz': Container
                }
            }
        },
        get_config=lambda x: x,
        container_clz=Container,
    )

    assert api.populate('GET', '/inner/cont/run')
