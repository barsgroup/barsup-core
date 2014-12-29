[![Build Status](https://travis-ci.org/barsgroup/barsup-core.svg?branch=master)](https://travis-ci.org/barsgroup/barsup-core)
[![Coverage Status](https://img.shields.io/coveralls/barsgroup/barsup-core.svg?style=flat)](https://coveralls.io/r/barsgroup/barsup-core?branch=master)
[![Latest Version](https://pypip.in/version/barsup-core/badge.svg?style=flat&text=version&0.1.8)](https://pypi.python.org/pypi/barsup-core/)
[![Supported Python versions](https://pypip.in/py_versions/barsup-core/badge.svg?style=flat)](https://pypi.python.org/pypi/barsup-core/)
[![Development Status](https://pypip.in/status/barsup-core/badge.svg?style=flat&beta)](https://pypi.python.org/pypi/barsup-core/)
[![License](https://pypip.in/license/barsup-core/badge.svg?style=flat)](https://pypi.python.org/pypi/barsup-core/)

* [WTF?](#markdown-header-wtf)
* [Возможности](#markdown-header-facilities)
* [Установка и запуск](#markdown-header-setup)
* [Описание конфигураций верхнего уровня контейнера](#markdown-header-description)
    * [Контроллеры](#markdown-header-controller)
    * [Сервисы](#markdown-header-service)
    * [Модели](#markdown-header-model)
    * [Сессия](#markdown-header-session)
    * [Отображение таблиц](#markdown-header-db-mapper)
    * [Опции API](#markdown-header-api-options)
    * [middleware](#markdown-header-middleware)
    * [initware](#markdown-header-initware)
* [Работа роутинга](#markdown-header-routing)
* [CLI как management команды](#markdown-header-cli)
* [Работа с аутентификацией и авторизацией](#markdown-header-auth)

## wtf
**barsup-core** - представляет собой базовые серверные реализации различных уровней rest-приложения, с возможностью декларативного описания функционала на базе [IoC](https://bitbucket.org/astynax/yadic).

## facilities

* строгая зависимость между уровнями приложения с отслеживанием утечек абстракции
* возможности расширять конфигурацию своими реализациями
* запуск контейнера как в режиме _вебсокетов_, так и в стандартном режиме _wsgi_
* возможности создания business-middleware и initware
* встроенные механизмы аутентификации и авторизации

## setup
Последнюю версию можно установить из [PYPI](https://pypi.python.org/pypi/barsup-core) командой:
```bash
$ pip install barsup-core
```
В качестве примера использования рекомендуется посмотреть [demo](https://bitbucket.org/barsgroup/barsup-demo) (с возможностью [очень быстрого запуска средствами Vagrant'a](https://bitbucket.org/barsgroup/barsup-demo/wiki/vagrant)), а так же примеры использования из [тестов](https://bitbucket.org/barsgroup/barsup-core/src/1998af93d9a30cbb3416ff356c33fce5657bab43/src/barsup/tests/?at=default)

## description
Диаграмма зависимостей уровней
![layers.png](https://bitbucket.org/repo/6nnLdx/images/1725052173-layers.png)

### controller
Контроллер представляет собой тонкий внешний интерфейс для работы с приложением. Имеет автоматическую генерацию url-ов по названию контроллера и методам. Так же включает в себя базовую параметров на уровне типов значений.

#### CRUD контроллер
Реализация: `barsup.controller.DictController`

Зависимости:

* `service` - связь с уровнем сервисов

Операции с одним элементом:

* get, `/read/{id:\d+}` - получение
* create, `/create/{id:\d+}` - создание
* update, `/update/{id:\d+}` - изменение
* destroy, `/destroy/{id:\d+}` - удаление

Операции с множеством элементом:

* read, `/read`, - получение списка
* bulk_create, `/create`, - создание
* bulk_update, `/update`, - изменение
* bulk_destroy, `/destroy`, - удаление

Контроллер можно вызывать из вне:
```python
# Через API:
data = api.call('SimpleController', 'update', id=4, {'name': 'Преступление и наказание', 'year': 1886})
# Через router:
data = api.populate('/SimpleController/update/4', {'name': 'Преступление и наказание', 'year': 1886})
```

Пример конфигурации:
```json
"controller": {
    "__default__": {
      "__realization__": "barsup.controller.DictController"
    },
    "Author": {
      "service": "AuthorService"
    },
    "Book": {
      "service": "BookService"
    },
    "UserBook": {
      "service": "UserBookService"
    }
}
```

## service
Уровень сервисов включает в себя основу для работы с бизнес-логикой приложения. Выполняет задачи:

* фильтрации
* сортировки
* группировки
* валидации на уровне бизнес-логики
* возможности ModelView
* Серриализация/Десерриализация - преобразование в объекты модели из базовые конструкций (*dict*, *list*) и наоборот

#### CRUD сервис
Реализация: `barsup.service.Service`

Зависимости:

* `model` - связь с уровнем моделей
* `adapters` - уровень адаптеров для возможности организации ModelView (по умолчанию один адаптер, преобразующий один в один параметры в поля модели)
* `include` - поля объекта для включения в результат на уровне адаптера (по-умолчанию - все поля)
* `exclude` - поля объекта для исключения из результат на уровне адаптера (по-умолчанию нет исключений)

**Adapters**

Список объектов, которые влияют на сохранение и извлечение данных из модели.
[Подробнее](#) про работу адаптеров.

Пример конфигурации:
```json
"service": {
    "__default__": {
      "__realization__": "barsup.service.Service",
      "adapters": []
    },
    "BookService": {
      "model": "book"
    },
    "AuthorService": {
      "model": "author",
      "adapters": ["FioSplitter"]
    },
    "UserBookService": {
      "model": "user_book"
    }
},
"adapters": {
    "FioSplitter": {
        "__realization__": "barsup.adapters.Splitter",
        "$to_name": "full_name",
        "$from_names": ["fname", "lname"]
    }
}
```

### model
Представляет собой отображение таблицы базы данных, создание query set'a с возможностью использования внешних и внутренних соединений (joins) и ограничение выборки (select) через *session*. Так же дает доступ, при необходимости, ко всем таблицам и их полям в базе данных через *db_mapper*.

Реализация `barsup.schema.Model`

Зависимости:

* `session` - связь с уровнем сессии
* `db_mapper` - связь с уровнем маппера базы данных
* `name` - название таблицы в базе данных
* `joins` - операции соединения с другими таблицами (по-умолчанию - нет соединений)
* `select` - список полей для отображения (по-умолчанию - все поля: _select *_)

Пример конфигурации:
```json
  "model": {
    "__default__": {
      "__realization__": "barsup.schema.Model",
      "db_mapper": "default",
      "session": "default"
    },
    "author": {
      "$name": "author"
    },
    "book": {
      "$name": "book"
    },
    "user_book": {
      "$name": "user_book",
      "$joins":[
        ["user_id", "==", "id", ["user", []]],
        ["book_id", "==", "id", ["book", []]]
      ],
      "$select": ["id", "book_id", "book.name", "user_id", "user.name", "user.login", "return_date"]
    },
```

### session
Решает задачу [Repository](http://techspot.zzzeek.org/2012/02/07/patterns-implemented-by-sqlalchemy/) для объектов в контексте sqlalchemy.

Реализации `barsup.session.PostgreSQLSession`, `barsup.session.InMemory`.

Зависимости:

* `login` - логин для подключения к бд
* `password` - пароль (пока в открытом виде) для подключения к бд
* `host` - хост для подключения к бд
* `port` - порт для подключения к бд
* `database` - название бд
* `echo` - логирование DML операций (по-умолчанию True)

Пример конфигурации:
```json
"session": {
    "default": {
        "__type__": "singleton",
        "__realization__": "barsup.session.PostgreSQLSession",
        "$login": "barsup",
        "$password": "barsup",
        "$database": "barsup"
    }
}
```

### db-mapper
Предоставляет доступ к таблицам в базе данных.

Зависимости:

* `path`- путь до файла конфигурации (по-умолчанию берется из переменной среды BUP_SCHEMA)

Пример конфигурации:
```json
  "db_mapper": {
    "default": {
      "__realization__": "barsup.schema.DBMapper",
      "__type__": "singleton"
    }
  }
```

### api-options
Контейнер для служебных конфигураций.

Зависимости:

* `middleware` - список middleware
* `initware` - список initware

Пример конфигурации:
```json
  "api_options": {
    "default": {
      "initware": [
        "list_actions"
      ],
      "middleware": [
        "log_errors_to_stderr",
        "access_check",
        "transact"
      ]
    }
  }
```

### middleware
Уровень обслуживающий входящие/исходящие request'ы.
![Middleware](https://bitbucket.org/repo/6nnLdx/images/3070979907-clack-middleware-2.png)

Доступные middleware:

* `log_errors_to_stderr` - логирование исключений
* `access_check` - аутентфикация и авторизация приложения
* `transact` - оборачивание запросов в транзакции

Пример конфигурации:
```json
  "middleware": {
    "__default__": {"__type__": "static"},
    "log_errors_to_stderr": {
      "__realization__": "barsup.middleware.log_errors_to_stderr"
    },
    "access_check": {
      "__type__": "singleton",
      "__realization__": "barsup.auth.middleware.access_check",
      "$authentication": "Authentication",
      "$authorization": "Authorization"
    },
    "transact": {
      "__type__": "singleton",
      "__realization__": "barsup.middleware.transact",
      "session": "default"
    }
  }
```

### initware

## routing

## cli

## auth