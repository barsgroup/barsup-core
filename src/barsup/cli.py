# coding:utf-8

import os
import sys
import json

from barsup.accli import AutoCompleteCLI
from barsup import core


class CLI(AutoCompleteCLI):

    @property
    def hierarchy(self):
        res = {}
        for ctr, act in self.api:
            res.setdefault(ctr, {})[act] = {}
        return res

    def __init__(self):
        try:
            self.cfg_file = os.environ['BUP_CONFIG']
        except KeyError:
            print("BUP_CONFIG anviront variable is not provided!")
            sys.exit(1)
        else:
            with open(self.cfg_file) as f:
                self.api = core.init(json.load(f)['container'])

    def _call(self, args):
        ctl, action, param = (args + ["{}"])[:3]
        res = self.api.call(ctl, action, **eval(param))
        print(json.dumps(res, indent=2, default=tuple))


if __name__ == '__main__':
    CLI().run()
