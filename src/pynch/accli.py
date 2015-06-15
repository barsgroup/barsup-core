# coding:utf-8
"""CLI-Application with bash-auto-completion."""

import os


class AutoCompleteCLI:

    """CLI-Application with bash-auto-completion.

    CLI-Application, поддерживающее механизм bash auto-completion
    для комманд.
    """

    EXIT_OK, EXIT_ERROR = 0, 1

    usage = ''

    hierarchy = {}

    @property
    def comp_line(self):
        """Значение переменной окружения $COMP_LINE.

        Возвращается в виде списка строк.
        """
        return os.environ['COMP_LINE'].split()[1:-1]

    def run(self, args=None):
        """Разбирает аргументы @args.

        Выполняет разбор аргументов и выводит список возможных
        команд, или же вызывает конкретную команду, если она указана.
        """
        exit_code = self.EXIT_OK

        if args:
            if args[0] == '--complete':
                if len(args) < 3:
                    self._out('Wrong "--complete" call!')
                    exit_code = self.EXIT_ERROR
                else:
                    itself = args[1]
                    if len(args) > 3:
                        partial, prev = args[2:]
                    else:
                        partial, prev = '', args[2]
                    for c in self._complete(
                        partial,
                        prev if prev != itself else '',
                        self.comp_line
                    ):
                        self._out(c)
            else:
                try:
                    self._call(args)
                except Exception as e:
                    self._out(str(e))
                    exit_code = self.EXIT_ERROR
        else:
            self._out(self.usage)

        return exit_code

    _out = staticmethod(print)

    def _call(self, args):
        """Обрабатывает введенные аргументы."""
        pass

    def _complete(self, partial, prev, args):
        """Возвращает список вариантов.

        Возвращает список доступных вариантов для дополнения
        аргументов, исходя из иерархии команд.
        """
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
