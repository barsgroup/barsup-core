# coding: utf-8
"""Тест работоспособности middleware авторизации в конфигурации
с несколькики уровнями вложенности модулей."""

import pytest

from barsup.core import init, ModuleContainer
from barsup.exceptions import Forbidden
from barsup.controller import Controller


class FakeAuth:
    """Сервис-заглушка, запоминающий контроллеры
    для которых проверяет права и способный отказать
    в правах заданному пользователю."""

    GOOD_USER, BAD_USER = 0, 1

    def __init__(self):
        """Конструктор."""
        self.controllers = set()

    def has_perm(self, uid, controller, _):
        """Возвращает наличие/отсутствие прав на выполнение
        некоего действия у указанного пользователя."""
        if uid == self.BAD_USER:
            return False
        self.controllers.add(controller)
        return True


def pop_uid(nxt, controller, action, uid, _context, **params):
    """Перемещает UID из параметров в контекст."""
    _context['uid'] = uid
    return nxt(controller, action, _context=_context, **params)


class EchoController(Controller):
    """Контроллер-заглушка."""

    @staticmethod
    def action(message: "str") -> r"/action":
        """Возвращает полученное сообщение обратно."""
        return message


def make_container(**provided):
    """Возвращает класс контейнера, умеющий предоставлять
    сущности, указанные в **provided."""

    class Container(ModuleContainer):
        """Контейнер, умеющий предоставлять часть сущностей
        без необходимости их импортирования штатным способом."""

        @staticmethod
        def _get_entity(name):
            """Возвращает контроллер-заглушку."""
            obj = provided.get(name)
            if obj is not None:
                return obj
            else:
                return ModuleContainer._get_entity(name)

    return Container


def test_module_authorization():
    """
    Проверяет работоспособность middleware авторизации
    в условиях конфигурации со вложенными модулями
    """
    auth = FakeAuth()

    api = init(
        config={
            'controller': {
                'm1': {
                    '__realization__': 'barsup.controller.ModuleController',
                    'module': 'm1'
                }
            },
            'api_options': {
                'default': {
                    'middleware': [
                        # pop_uid обеспечивает для authorization
                        # наличие UID, указанного в параметрах вызова экшна
                        'pop_uid',
                        'authorization'
                    ]
                }
            },
            'middleware': {
                'authorization': {
                    '__realization__': 'barsup.auth.middleware.authorization',
                    '$auth': auth
                },
                'pop_uid': {
                    '__realization__': 'POP_UID',
                    '__type__': 'static'
                }
            },
            'module': {
                'm1': {
                    '$config': {
                        'controller': {
                            'm2': {
                                '__realization__': (
                                    'barsup.controller.ModuleController'),
                                'module': 'm2'
                            }
                        },
                        'api_options': {
                            'default': {
                                'middleware': ['../authorization']
                            }
                        },
                        'module': {
                            'm2': {
                                '$config': {
                                    'controller': {
                                        'cont': {
                                            '__realization__': 'CONT'
                                        }
                                    },
                                    'api_options': {
                                        'default': {
                                            'middleware': [
                                                '../../authorization'
                                            ]
                                        }
                                    },
                                },
                                '$get_config': lambda x: x,
                                '$container_clz': make_container(
                                    CONT=EchoController
                                )
                            }
                        }
                    },
                    '$get_config': lambda x: x
                }
            }
        },
        get_config=lambda x: x,
        container_clz=make_container(POP_UID=pop_uid)
    )

    def call_for(uid, message):
        return api.populate('/m1/m2/cont/action', uid=uid, message=message)

    assert call_for(FakeAuth.GOOD_USER, "Hi!") == "Hi!"

    with pytest.raises(Forbidden):
        call_for(FakeAuth.BAD_USER, "Hello!")

    assert auth.controllers == set(['m1/m2/cont'])
