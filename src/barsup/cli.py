# coding:utf-8

import os
import sys
import json

from barsup import core


class AutoCompleteCLI:
    usage = ''

    hierarchy = {}

    def run(self, args=None):
        args = sys.argv[1:] if args is None else args
        if args:
            if args[0] == '--complete':
                itself = args[1]
                if len(args) > 3:
                    partial, prev = args[2:]
                else:
                    partial, prev = '', args[2]
                for c in self._complete(
                    partial,
                    prev if prev != itself else '',
                    os.environ['COMP_LINE'].split()[1:-1]
                ):
                    print(c)
            else:
                self._call(args)
        else:
            print(self.usage)

    def _call(self, args):
        pass

    def _complete(self, partial, prev, args):
        data = self.hierarchy
        for key in args:
            try:
                data = data[key]
            except KeyError:
                return

        pred = (lambda x: x.startswith(partial) if partial else lambda x: True)

        if prev and not partial:
            data = data.get(prev, [])

        for i in data:
            if pred(i):
                yield i


class CLI(AutoCompleteCLI):
    @property
    def hierarchy(self):
        res = {}
        for ctr, act in self.api:
            res.setdefault(ctr, {})[act] = {}
        return res

    def __init__(self, cfg_file):
        if not cfg_file:
            print("BUP_CONFIG environ variable is not provided!")
            sys.exit(1)
        else:
            self.api = core.init(cfg_file)

    def _call(self, args):
        ctl, action, param = (args + ["{}"])[:3]
        res = self.api.call(ctl, action, **eval(param))
        print(json.dumps(res, indent=2, default=tuple))


if __name__ == '__main__':
    CLI(os.environ.get('BUP_CONFIG')).run()
