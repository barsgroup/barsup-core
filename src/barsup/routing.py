# -*- coding: utf-8 -*-

import routes
import simplejson as json


PARAM_PARSERS = {
    'json': json.loads,
    'str': str,
    'int': int,
    'list': list,
    'dict': dict
}


class Router:
    def __init__(self, call_api, cont, controller_group):
        self._mapper = routes.Mapper()
        self._call_api = call_api
        self._cont = cont
        self._group = controller_group
        self._param_decls = {}

        for controller, conf, realization in cont.itergroup(controller_group):
            mapper = self._mapper.submapper(
                path_prefix='/' + controller.lower())
            for action_decl in getattr(realization, 'actions'):
                route, action, params = (action_decl + (None,))[:3]
                mapper.connect(route, controller=controller, action=action)
                if params:
                    try:
                        parsers = dict(
                            (k, PARAM_PARSERS[v])
                            for k, v in params.items()
                        )
                    except KeyError:
                        raise ValueError(
                            'Unknown action param type in %s!' % controller)
                    self._param_decls[(controller, action)] = parsers

    def populate(self, web_session_id, key, params):
        """
        Populates the url-like API-key as action of some controller
        :web_session_id: web session id
        :key: API-key
        :params: action params
        """
        dest = self._mapper.match(key)
        if not dest:
            raise ValueError('Wrong key: "%s"!' % key)

        controller_name, action_name = map(dest.pop, ('controller', 'action'))

        parsed_params = {}
        parsers = self._param_decls.get((controller_name, action_name), {})
        for name, value in params.items():
            if name == 'format':
                continue
            try:
                parser = parsers[name]
            except KeyError:
                raise ValueError(
                    'Undeclared parameter "%s" (%s.%s)'
                    % (name, controller_name, action_name)
                )
            try:
                parsed_params[name] = parser(value)
            except (TypeError, ValueError):
                raise ValueError(
                    'Wrong value for param "%s" (%s.%s)'
                    % (name, controller_name, action_name)
                )

        dest.update(parsed_params)
        dest['web_session_id'] = web_session_id
        return self._call_api(controller_name, action_name, **dest)


__all__ = (Router,)


if __name__ == '__main__':

    class CalcController:

        actions = (
            ('/{x:\d+}/{y:\d+}/sum', 'sum'),
            ('/{x:\d+}/{y:\d+}/mul', 'mul'),
            ('/{x:\d+}/double', 'double'),
        )

        @staticmethod
        def sum(x, y, uid):
            return int(x) + int(y)

        @staticmethod
        def mul(x, y, uid):
            return int(x) * int(y)

        @staticmethod
        def double(x, uid):
            return int(x) * 2

    class StrController:

        actions = (
            ('/{s:.+}/upper', 'upper'),
            ('/{s:.+}/lower', 'lower'),
        )

        @staticmethod
        def upper(s, uid):
            return s.upper()

        @staticmethod
        def lower(s, uid):
            return s.lower()

    class Parametrized:

        actions = (
            ('/{x:\d+}/add', 'add',
             {'x': 'int', 'y': 'int', 'msg': 'str', 'raw': 'json'}),
        )

        @staticmethod
        def add(uid, x, y=42, msg='Unknown', raw=None):
            d = {'x': x, 'y': y, 'msg': msg}
            d.update(raw or {})
            return "%s:%s:%d" % (d['msg'], d['x'], d['y'])

    class FakeContainer:
        @staticmethod
        def get(grp, name):
            return {
                'rpc': {
                    'Calc': CalcController,
                    'Str': StrController,
                    'Parametrized': Parametrized,
                }
            }[grp][name]

        @staticmethod
        def itergroup(group):
            yield ('Calc', {}, CalcController)
            yield ('Str', {}, StrController)
            yield ('Parametrized', {}, Parametrized)

    def fake_api(ctl, act, **kwargs):
        return getattr({
            'Calc': CalcController,
            'Str': StrController,
            'Parametrized': Parametrized,
        }[ctl], act)(**kwargs)

    router = Router(fake_api, FakeContainer(), 'rpc')
    print(router._mapper)

    assert router.populate(0, '/calc/10/2/sum', {}) == 12
    assert router.populate(0, '/calc/10/2/mul', {}) == 20
    assert router.populate(0, '/calc/7/double', {}) == 14
    assert router.populate(0, '/str/Hello!/upper', {}) == 'HELLO!'
    assert router.populate(0, '/str/Hello!/lower', {}) == 'hello!'

    assert router.populate(0, '/parametrized/10/add', {}) == 'Unknown:10:42'

    assert router.populate(
        0, '/parametrized/202/add', {'y': '404', 'msg': '>>>'}
    ) == '>>>:202:404'

    assert router.populate(
        0, '/parametrized/1000/add', {'raw': '{"x": "0", "y": 0, "msg": "0"}'}
    ) == '0:0:0'

    def throws(excs, fn, *args):
        try:
            fn(*args)
        except excs as e:
            print(e)
        except Exception as e:
            raise AssertionError('Thrown unexpected %r!' % e)

    throws(ValueError, router.populate, 0, '/parametrized/1000/add', {'z': 1})
    throws(ValueError,
           router.populate, 0, '/parametrized/1000/add', {'y': 'asd'})
    throws(ValueError,
           router.populate, 0, '/parametrized/1000/add', {'raw': '!'})
