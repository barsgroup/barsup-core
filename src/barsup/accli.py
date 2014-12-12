# coding:utf-8

from __future__ import print_function
import sys
import os


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

        pred = (lambda x: x.startswith(partial)
                if partial else
                lambda x: True)

        if prev and not partial:
            data = data.get(prev, [])

        for i in data:
            if pred(i):
                yield i


if __name__ == '__main__':
    class CLI(AutoCompleteCLI):
        hierarchy = {
            'show': {
                'version': {},
                'info': {},
                'help': {
                    'about': {},
                    'usage': {}
                }
            },
            'config': {
                'editor': {},
                'environment': {},
            }
        }

    CLI().run()
