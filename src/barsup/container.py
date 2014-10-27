# -*- coding: utf-8 -*-
"""
Простой IoC-контейнер
"""

from importlib import import_module
import re


class Injectable(type):
    """
    Добавляет в класс конструктор,
    получающий зависимости в качестве параметров
    и сохраняющий их в атрибуты
    """

    def __new__(cls, name, bases, dic):
        deps = dic.setdefault('depends_on', tuple())
        if deps and '__init__' not in dic:
            # формирование конструктора
            init = eval("lambda self, %s: %s" % (
                ','.join(deps),
                ' or '.join(
                    'setattr(self, "{0}", {0})'.format(d)
                    for d in deps)
            ))
            dic['__init__'] = init
        return super(Injectable, cls).__new__(cls, name, bases, dic)


class Container(object):
    """
    IoC Container для конфигурирования сервисов
    """
    _TYPES = ('static', 'singleton', None)

    def __init__(self, config):
        """
        :param filename: Имя json-файла с конфигурацией
        :type filename: str
        """
        errors = self.collect_errors(config)
        if errors:
            raise ValueError('\n'.join(['Config errors:'] + errors))
        self._config = self._denormalize(config)
        self._entity_cache = {}
        self._singletones = {}

    @staticmethod
    def _denormalize(config):
        """
        Возвращает денормализованную конфигурацию
        :param config: исходная конфигурация
        :type param: dict
        """
        def apply_if(a, b):
            for bk, bv in b.iteritems():
                av = a.get(bk)
                if av is None:
                    a[bk] = bv
                else:
                    av_is_dict, bv_is_dict = (
                        isinstance(av, dict), isinstance(bv, dict))
                    if av_is_dict and bv_is_dict:
                        apply_if(av, bv)
                    elif av_is_dict or bv_is_dict:
                        raise ValueError(
                            'Structures of plan and cusomization must match!')
                    else:
                        a[bk] = bv
            return a

        result = {}
        for sect, elems in config.iteritems():
            plan = elems.get('__default__', {})
            section = result[sect] = {}
            for el_name, customization in elems.iteritems():
                if el_name != '__default__':
                    section[el_name] = apply_if(plan.copy(), customization)
        return result

    @staticmethod
    def _get_entity(name):
        """
        Возвращает сущность (обычно - класс) по полному имени
        """
        if '.' not in name:
            raise ValueError('Entity name must be the fully qualified!')
        attr_name = name.split('.')[-1]
        module = import_module(name[:-(len(attr_name) + 1)])
        return getattr(module, attr_name)

    def _get_blueprint(self, group, name):
        """
        Возвращает конфигурацию элемента группы
        и конкретную сущность, его реализующую.
        Сущности в процессе кэшируются.
        """
        blueprint = self._config[group][name]
        key = (group, name)
        return (
            blueprint,
            self._entity_cache.get(key) or self._entity_cache.setdefault(
                key, self._get_entity(blueprint['__realization__']))
        )

    def itergroup(self, group):
        """
        Возвращает итератор пар (имя_элемента, конфигурация, реализация)
        :param group: группа
        :type group: str
        """
        if group not in self._config:
            raise KeyError("Unknown group: %r!" % group)
        return (
            (i,) + self._get_blueprint(group, i)
            for i in self._config[group]
        )

    def get(self, group, name):
        """
        Возвращает сконфигурированный элемент группы (экземпляр)
        :param group: группа элементов
        :type group: str
        :param name: имя элемента группы
        :type name: str
        """
        # try:
        blueprint, realization = self._get_blueprint(group, name)
        # except KeyError:
        #     raise KeyError("%s:%s is not configured!" % (group, name))

        typ = blueprint.get('__type__')

        if typ == 'static':
            result = realization
        else:
            is_singleton = typ == 'singleton'
            if is_singleton:
                result = self._singletones.get((group, name))
            if not is_singleton or not result:
                deps = {}
                for dep_group, dep_name in blueprint.iteritems():
                    if dep_group.startswith('_'):
                        continue
                    elif dep_group.startswith('$'):
                        deps[dep_group[1:]] = dep_name
                    else:
                        deps[dep_group] = self.get(dep_group, dep_name)
                result = realization(**deps)
                if is_singleton:
                    self._singletones[(group, name)] = result
        return result

    @classmethod
    def collect_errors(cls, cfg):
        """
        Возвращает список ошибок в строковом представлении
        """
        errors = []

        def wrong(what, names):
            errors.append('%r is a wrong %s name!' % (':'.join(names), what))

        is_ident = re.compile(r'(?i)^[a-z]\w*$').match

        for group, elems in cfg.iteritems():
            if not is_ident(group):
                wrong('group', (group,))
            for el, cfg in elems.iteritems():
                if not is_ident(el) and el != '__default__':
                    wrong('element', (group, el))
                for k, v in cfg.iteritems():
                    if not (
                        is_ident(k) or
                        (is_ident(k[1:]) and k[0] == '$') or
                        k in ('__realization__', '__type__')
                    ):
                        wrong('attr', (group, el, k))
                    if k == '__type__' and v not in cls._TYPES:
                        wrong('type', (group, el, k))
        return errors


__all__ = (Container,)


if __name__ == '__main__':

    # ======================
    # тест валидации конфига
    assert Container.collect_errors({'$grp': {}})
    assert Container.collect_errors({'grp': {'$$name': {}}})
    assert Container.collect_errors({'grp': {'$name': {}}})
    assert Container.collect_errors({'grp': {'name': {'$$attr': ''}}})
    assert Container.collect_errors({'grp': {'name': {'$': ''}}})
    assert Container.collect_errors({'grp': {'name': {'__type__': 'asdf'}}})
    assert Container.collect_errors(
        {'grp': {'name': {'__realizationn__': 'asdf'}}})

    # ============================================
    # конфигурирование экземпляров с зависимостями
    class Named(object):
        def __str__(self):
            return self.name

    class Engine(object):
        def __init__(self, fuel):
            self.fuel = fuel

        def __str__(self):
            return "%s on %s" % (self.name, self.fuel)

    class Vehicle(object):
        __metaclass__ = Injectable
        depends_on = ('actuator', 'engine')

        def __str__(self):
            return "The vehicle, driven by %s, which powered by %s" % (
                self.actuator, self.engine)

    entities = {
        'demo.veh.Vehicle': Vehicle,
        'demo.act.Wheel': type('Wheel', (Named,), {'name': 'wheel'}),
        'demo.act.Rotor': type('Rotor', (Named,), {'name': 'rotor'}),
        'demo.fue.Gasoline': 'Gasoline',
        'demo.fue.Coal': 'Coal',
        'demo.eng.Diesel': type('Diesel', (Engine,), {'name': 'diesel'}),
        'demo.eng.SteamEngine': type(
            'SteamEngine', (Engine,), {'name': 'steam engine'}),
    }

    config = {
        'vehicle': {
            '__default__': {
                '__realization__': 'demo.veh.Vehicle',
                'engine': 'Diesel'
            },
            'Truck': {'actuator': 'Wheel'},
            'Boat': {'actuator': 'Rotor', 'engine': 'SteamEngine'}
        },
        'actuator': {
            'Wheel': {'__realization__': 'demo.act.Wheel'},
            'Rotor': {'__realization__': 'demo.act.Rotor'},
        },
        'engine': {
            '__default__': {
                'fuel': 'Gasoline'
            },
            'Diesel': {'__realization__': 'demo.eng.Diesel'},
            'SteamEngine': {
                '__realization__': 'demo.eng.SteamEngine',
                'fuel': 'Coal'
            }
        },
        'fuel': {
            # элементы с as-is не инстанцируются, а предоставляются "как есть"
            '__default__': {'__type__': 'static'},
            'Gasoline': {'__realization__': 'demo.fue.Gasoline'},
            'Coal': {'__realization__': 'demo.fue.Coal'},
        }
    }

    cont = type('LocalContainer', (Container,), {
        '_get_entity': staticmethod(entities.get)}
    )(config)

    for name, _, realization in cont.itergroup('vehicle'):
        print '%s :: %s' % (name, realization.__name__)
        print '  ', cont.get('vehicle', name)

    # ===========================================
    # тест на использование статичкских элементов
    def fake_imports(modules):
        def getter(key):
            m, a = key.split('.')
            return modules[m][a]
        return getter

    cont = type('C', (Container,), {'_get_entity': staticmethod(
        fake_imports({
            'module': {
                'square': lambda arg: arg * arg,
                'CONST': 5
            }
        }))}
    )({
        'function': {
            'f': {
                '__realization__': 'module.square',
                'arg': 'x',
            }
        },
        'arg': {
            'x': {'__realization__': 'module.CONST', '__type__': 'static'}
        }
    })
    assert cont.get('function', 'f') == 25

    # ========================
    # тест singleton-элементов

    cont = type('LocalContainer', (Container,), {
        '_get_entity': staticmethod({'List': list}.get)}
    )({
        'container': {
            'list': {
                '__type__': 'singleton',
                '__realization__': 'List'
            }
        }
    })
    cont.get('container', 'list').append(1)
    cont.get('container', 'list').append(2)
    assert cont.get('container', 'list') == [1, 2]

    # =====================================
    # тест подстановки статичных аргументов

    cont = type('LocalContainer', (Container,), {
        '_get_entity': staticmethod({'Func': lambda x, y: x + y}.get)}
    )({
        'results': {
            'sum_x_y': {
                '__realization__': 'Func',
                '$x': 20,
                '$y': 22,
            }
        }
    })
    assert cont.get('results', 'sum_x_y') == 42
