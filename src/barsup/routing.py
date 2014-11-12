# -*- coding: utf-8 -*-

import routes


class Router(object):
    def __init__(self, cont, controller_group):
        self._mapper = routes.Mapper()
        self._cont = cont
        self._group = controller_group

        for controller, conf, realization in cont.itergroup(controller_group):
            mapper = self._mapper.submapper(
                path_prefix='/' + controller.lower())
            for route, action in getattr(realization, 'actions'):
                mapper.connect(route, controller=controller, action=action)

    def populate(self, uid, key, params):
        """
        Populates the url-like API-key as action of some controller
        :uid: UserID
        :key: API-key
        :params: action params
        """
        dest = self._mapper.match(key)
        if not dest:
            raise ValueError('Wrong key: "%s"!' % key)
        controller_name, action_name = map(dest.pop, ('controller', 'action'))
        controller = self._cont.get(self._group, controller_name)
        controller.uid = uid
        try:
            action = getattr(controller, action_name)
        except AttributeError:
            raise ValueError(
                "The \"%s\" controller don't have an action \"%s\"!"
                % (controller_name, action_name))
        dest['params'] = params
        return action(**dest)


__all__ = (Router,)


if __name__ == '__main__':

    class CalcController(object):

        actions = (
            ('/{x:\d+}/{y:\d+}/sum', 'sum'),
            ('/{x:\d+}/{y:\d+}/mul', 'mul'),
            ('/{x:\d+}/double', 'double'),
        )

        @staticmethod
        def sum(x, y, **params):
            return int(x) + int(y)

        @staticmethod
        def mul(x, y, **params):
            return int(x) * int(y)

        @staticmethod
        def double(x, **params):
            return int(x) * 2

    class StrController(object):

        actions = (
            ('/{s:.+}/upper', 'upper'),
            ('/{s:.+}/lower', 'lower'),
        )

        @staticmethod
        def upper(s, **params):
            return s.upper()

        @staticmethod
        def lower(s, **params):
            return s.lower()

    class FakeContainer(object):
        @staticmethod
        def get(grp, name):
            return {
                'rpc': {
                    'Calc': CalcController,
                    'Str': StrController
                }
            }[grp][name]

        @staticmethod
        def itergroup(group):
            yield ('Calc', {}, CalcController)
            yield ('Str', {}, StrController)

    router = Router(FakeContainer(), 'rpc')
    print router._mapper
    assert router.populate(0, '/calc/10/2/sum', {}) == 12
    assert router.populate(0, '/calc/10/2/mul', {}) == 20
    assert router.populate(0, '/calc/7/double', {}) == 14
    assert router.populate(0, '/str/Hello!/upper', {}) == 'HELLO!'
    assert router.populate(0, '/str/Hello!/lower', {}) == 'hello!'
