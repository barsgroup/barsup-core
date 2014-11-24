# -*- coding: utf-8 -*-

from os import environ, getcwd, path
from sys import exit

CMD_SERVER, CMD_WORKER = COMMANDS = ('server', 'worker')


def run(command, params):
    """
    Запускает компонент системы
    :param params: словарь конфигурации проекта
    :type params: dict
    :params component: компонент системы "server", "worker"
    :type component: string
    """
    assert command in COMMANDS

    # мерж умолчательного конфига и конкретного
    def merge(d1, d2):
        return d1.update(d2) or d1

    if command == CMD_SERVER:
        import barsup.server as module
    elif command == CMD_WORKER:
        import barsup.worker as module

    module.run(**merge(module.DEFAULT_PARAMS, params))


if __name__ == '__main__':
    from sys import argv
    import json
    args = argv[1:]
    if len(args) not in (1, 2) or args[0] not in COMMANDS:
        print(
            "Usage: bup_start <command> <config-file>\nCommands: %s"
            % ','.join(COMMANDS))
    else:
        cmd, fname = (args + [None])[:2]

        # если путь не указан, то файл ищется в папке,
        # указанной в BUP_PATH, а если оная не указана,
        # то в текущей папке
        if not fname:
            directory = environ.get('BUP_PATH') or getcwd()
            fname = path.join(directory, cmd + '.json')

        try:
            cfg = open(fname).read()
        except IOError:
            print('Can''t open file "%s"' % fname)
            exit(1)

        try:
            params = json.loads(cfg)
        except ValueError:
            print("Bad JSON format!")
        else:
            run(cmd, params)
