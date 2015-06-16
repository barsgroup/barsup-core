.. image:: https://travis-ci.org/barsgroup/pynch-core.svg?branch=master
    :target: https://travis-ci.org/barsgroup/pynch-core
    :alt: Tests

.. image:: https://img.shields.io/coveralls/barsgroup/pynch-core.svg?style=flat
    :target: https://coveralls.io/r/barsgroup/pynch-core?branch=master
    :alt: Coverage

WTF
---

**pynch-core** - представляет собой базовые серверные реализации различных
уровней rest-приложения, с возможностью декларативного описания функционала
на базе `IoC <https://bitbucket.org/astynax/yadic>`_.

Возможности
-----------

* строгая зависимость между уровнями приложения с отслеживанием утечек абстракции
* возможности расширять конфигурацию своими реализациями
* запуск контейнера как в режиме *вебсокетов*, так и в стандартном режиме *wsgi*
* возможности создания business-middleware и initware
* встроенные механизмы аутентификации и авторизации

Установка
---------

Последнюю версию можно установить из `PYPI <https://pypi.python.org/pypi/pynch-core>`_ командой::

    $ pip install pynch-core

В качестве примера использования рекомендуется посмотреть
`demo <https://bitbucket.org/barsgroup/pynch-demo>`_
(с возможностью `очень быстрого запуска средствами Vagrant'a
<https://bitbucket.org/barsgroup/pynch-demo/wiki/vagrant>`_ ),
а так же примеры использования из `тестов
<https://bitbucket.org/barsgroup/pynch-core/src/1998af93d9a30cbb3416ff356c33fce5657bab43/src/pynch/tests/?at=default>`_


`Подробная документация <https://bitbucket.org/barsgroup/pynch-core/wiki/Home>`_
