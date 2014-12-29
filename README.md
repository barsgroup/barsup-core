[![Build Status](https://travis-ci.org/barsgroup/barsup-core.svg?branch=master)](https://travis-ci.org/barsgroup/barsup-core)
[![Coverage Status](https://img.shields.io/coveralls/barsgroup/barsup-core.svg?style=flat)](https://coveralls.io/r/barsgroup/barsup-core?branch=master)
[![Latest Version](https://pypip.in/version/barsup-core/badge.svg?style=flat&text=version&0.1.8)](https://pypi.python.org/pypi/barsup-core/)
[![Supported Python versions](https://pypip.in/py_versions/barsup-core/badge.svg?style=flat)](https://pypi.python.org/pypi/barsup-core/)
[![Development Status](https://pypip.in/status/barsup-core/badge.svg?style=flat&beta)](https://pypi.python.org/pypi/barsup-core/)
[![License](https://pypip.in/license/barsup-core/badge.svg?style=flat)](https://pypi.python.org/pypi/barsup-core/)

## WTF
**barsup-core** - представляет собой базовые серверные реализации различных уровней rest-приложения, с возможностью декларативного описания функционала на базе [IoC](https://bitbucket.org/astynax/yadic).

## Возможности

* строгая зависимость между уровнями приложения с отслеживанием утечек абстракции
* возможности расширять конфигурацию своими реализациями
* запуск контейнера как в режиме _вебсокетов_, так и в стандартном режиме _wsgi_
* возможности создания business-middleware и initware
* встроенные механизмы аутентификации и авторизации

## Установка
Последнюю версию можно установить из [PYPI](https://pypi.python.org/pypi/barsup-core) командой:
```bash
$ pip install barsup-core
```
В качестве примера использования рекомендуется посмотреть [demo](https://bitbucket.org/barsgroup/barsup-demo) (с возможностью [очень быстрого запуска средствами Vagrant'a](https://bitbucket.org/barsgroup/barsup-demo/wiki/vagrant)), а так же примеры использования из [тестов](https://bitbucket.org/barsgroup/barsup-core/src/1998af93d9a30cbb3416ff356c33fce5657bab43/src/barsup/tests/?at=default)

[Подробная документация](https://bitbucket.org/barsgroup/barsup-core/wiki/Home)