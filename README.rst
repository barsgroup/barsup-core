.. image:: https://travis-ci.org/barsgroup/barsup-core.svg?branch=master
    :target: https://travis-ci.org/barsgroup/barsup-core
    :alt: Tests

.. image:: https://img.shields.io/coveralls/barsgroup/barsup-core.svg?style=flat
    :target: https://coveralls.io/r/barsgroup/barsup-core?branch=master
    :alt: Coverage

.. image:: https://pypip.in/version/barsup-core/badge.svg?style=flat&text=version&0
    :target: https://pypi.python.org/pypi/barsup-core/
    :alt: Latest Version

.. image:: https://pypip.in/py_versions/barsup-core/badge.svg?style=flat
    :target: https://pypi.python.org/pypi/yadic/
    :alt: Supported Python versions

.. image:: https://pypip.in/status/barsup-core/badge.svg?style=flat
    :target: https://pypi.python.org/pypi/yadic/
    :alt: Development Status

.. image:: https://pypip.in/license/barsup-core/badge.svg?style=flat
    :target: https://pypi.python.org/pypi/yadic/
    :alt: License

WTF
---

**barsup-core** - представляет собой базовые серверные реализации различных уровней rest-приложения, с возможностью декларативного описания функционала на базе `IoC <https://bitbucket.org/astynax/yadic>`_.

Возможности
-----------

* строгая зависимость между уровнями приложения с отслеживанием утечек абстракции
* возможности расширять конфигурацию своими реализациями
* запуск контейнера как в режиме _вебсокетов_, так и в стандартном режиме _wsgi_
* возможности создания business-middleware и initware
* встроенные механизмы аутентификации и авторизации

Установка
---------

Последнюю версию можно установить из [PYPI](https://pypi.python.org/pypi/barsup-core) командой::

    $ pip install barsup-core

В качестве примера использования рекомендуется посмотреть `demo <https://bitbucket.org/barsgroup/barsup-demo>`_ (с возможностью `очень быстрого запуска средствами Vagrant'a <https://bitbucket.org/barsgroup/barsup-demo/wiki/vagrant>`_ ), а так же примеры использования из `тестов <https://bitbucket.org/barsgroup/barsup-core/src/1998af93d9a30cbb3416ff356c33fce5657bab43/src/barsup/tests/?at=default>`_

`Подробная документация <https://bitbucket.org/barsgroup/barsup-core/wiki/Home>`_