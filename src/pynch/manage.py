# coding: utf-8
"""Auto-completing CLI-Application для configurable commands."""

import sys

import plac

from pynch.accli import AutoCompleteCLI
from pynch.core import init
from pynch.util import get_config_from_env


class ManagementCLI(AutoCompleteCLI):

    """Auto-completing CLI-Application для configurable commands."""

    COMMAND_GROUP = 'management'

    @property
    def hierarchy(self):
        """Возвращает список management commands."""
        return {
            k[0]: {} for k in
            self.cont.itergroup(self.COMMAND_GROUP)
        }

    def __init__(self, config_file=None):
        """Конструирует ManagementCLI."""
        api = init(config_file or get_config_from_env())
        self.cont = api._container

    def _call(self, args):
        command = args[0]
        cmd = self.cont.get(self.COMMAND_GROUP, command)
        plac.call(cmd, args[1:])


if __name__ == '__main__':
    sys.exit(ManagementCLI().run(sys.argv[1:]))
