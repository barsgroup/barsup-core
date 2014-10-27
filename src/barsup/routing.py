# -*- coding: utf-8 -*-

import routes


class Router(object):
    def __init__(self, cont, controller_group, config):
        self._mapper = routes.Mapper()
        self._cont = cont
        self._group = controller_group

        def build(mapper, data, controller, path):
            for act in data.get('__actions__', []):
                mapper.link(act)
            for k, v in data.iteritems():
                if k in ('__actions__', '__controller__'):
                    continue
                sub_controller = v.get('__controller__')
                if not sub_controller and not controller:
                    raise ValueError(
                        'No controller specified for the "%s%s" route!'
                        % (path, k)
                    )
                kwargs = {'path': path + k, 'data': v}
                if sub_controller:
                    build(mapper=mapper.submapper(
                        path_prefix=k, controller=sub_controller),
                        controller=sub_controller, **kwargs)
                else:
                    build(mapper=mapper.submapper(path_prefix=k),
                          controller=controller, **kwargs)

        build(self._mapper, config, None, '')

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

    router = Router(FakeContainer(), 'rpc', {
        '/calc': {
            '__controller__': 'Calc',
            r'/{x:\d+}': {
                '__actions__': ['double'],
                r'/{y:\d+}': {
                    '__actions__': ['sum', 'mul']
                }
            }
        },
        '/str': {
            '__controller__': 'Str',
            r'/{s:.+}': {
                '__actions__': ['upper', 'lower']
            }
        }
    })

    #print router._mapper
    assert router.populate(0, '/calc/10/2/sum', {}) == 12
    assert router.populate(0, '/calc/10/2/mul', {}) == 20
    assert router.populate(0, '/calc/7/double', {}) == 14
    assert router.populate(0, '/str/Hello!/upper', {}) == 'HELLO!'
    assert router.populate(0, '/str/Hello!/lower', {}) == 'hello!'
