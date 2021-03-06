# coding:utf-8
"""Autocomplete CLI for controllers/actions."""

import sys
import json

from pynch.accli import AutoCompleteCLI
from pynch.util import get_config_from_env
from pynch.core import init


class APICLI(AutoCompleteCLI):

    """Autocomplete CLI for controllers/actions."""

    @property
    def hierarchy(self):
        """Возвращает иерархию controllers/actions."""
        res = {}
        for ctr, act in self.fend.api:
            res.setdefault(ctr, {})[act] = {}
        return res

    def __init__(self, config_file=None):
        """Принимает опциональное имя файла конфигурации."""
        self.fend = init(config_file or get_config_from_env())

    def _call(self, args):
        ctl, action, param = (args + ["{}"])[:3]
        res = self.fend.api.call(ctl, action, **eval(param))
        self._out(json.dumps(res, indent=2, default=tuple))


if __name__ == '__main__':
    sys.exit(APICLI().run(sys.argv[1:]))
