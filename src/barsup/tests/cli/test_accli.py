# coding: utf-8

from barsup import accli


class CLI(accli.AutoCompleteCLI):

    usage = "Fake ACCLI"

    def __init__(self, comp_line, buf):
        self._comp_line = comp_line
        self._out = buf.append

    @property
    def comp_line(self):
        return self._comp_line

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

    def _call(self, *args):
        self._out(args)

    @classmethod
    def test(cls, comp_line, *args):
        """Выполняет вызов CLI с указанными аргументами.

        Возвращает результат вызова в виде
        (список вывода, код возврата).
        """
        buf = []
        exit_code = cls(comp_line, buf).run(args)
        return list(sorted(buf)), exit_code


def test_usage_output():
    """Проверяет вывод справки."""

    assert CLI.test([]) == ([CLI.usage], 0)


def test_wrong_completion_call():
    """Проверяет поведение при неправильном вызове автодополнения."""

    assert CLI.test([], '--complete')[1] == CLI.EXIT_ERROR


def test_completion():
    """Проверяет автодополнение."""

    assert CLI.test(
        [], '--complete', '', ''
    ) == (
        ['config', 'show'], CLI.EXIT_OK
    )

    # !TODO!
    # assert CLI.test(
    #     [], '--complete', '', 'co'
    # ) == (
    #     ['config'], CLI.EXIT_OK
    # )
