# -*- coding: utf-8 -*-

CMP_SERVER, CMP_WORKER = COMPONENTS = ('server', 'worker')


def main(component, params):
    """
    Запускает компонент системы
    :param params: словарь конфигурации проекта
    :type params: dict
    :params component: компонент системы "server", "worker"
    :type component: string
    """
    assert component in COMPONENTS

    # мерж умолчательного конфига и конкретного
    def merge(d1, d2):
        return d1.update(d2) or d1

    if component == CMP_SERVER:
        import server as module
    elif component == CMP_WORKER:
        import worker as module

    print module.DEFAULT_PARAMS
    module.run(**merge(module.DEFAULT_PARAMS, params))


if __name__ == '__main__':
    from sys import argv
    import json
    args = argv[1:]
    if len(args) < 2 or args[0] not in COMPONENTS:
        print (
            "Usage: start <component> <config-file>\nComponents: %s"
            % ','.join(COMPONENTS))
    else:
        main(args[0], json.load(open(args[1])))
