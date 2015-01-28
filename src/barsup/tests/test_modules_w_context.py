# coding: utf-8

from barsup.core import init, ModuleContainer
from barsup.tests.test_middleware import (
    ensure_presense_of,
    add_to_context
)


class Container(ModuleContainer):

    class Controller:

        actions = (('/run', 'run', {}),)

        @staticmethod
        def run():
            pass

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
                    '__realization__': 'barsup.controller.ModuleController',
                    'module': 'inner'
                }
            },
            'api_options': {
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
                        'api_options': {
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

    assert api.populate('/inner/cont/run') is None
