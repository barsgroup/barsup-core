# coding: utf-8
import pytest

import barsup.exceptions as exc
from barsup.tests import create_api
from barsup.tests.auth import ADMIN_SESSION, USER_SESSION


get_api = create_api('auth', 'api.json')


@get_api
def test_without_session(api):
    """
    Пустой сессионный ключ
    """
    with pytest.raises(exc.Unauthorized):
        api.call("User", 'create', data={
            "login": "test",
            "email": "test@test.com",
            "password": "test"
        })


@get_api
def test_bad_session(api):
    """
    Неправильная сессия
    """
    with pytest.raises(exc.Unauthorized):
        api.call("User", 'create', data={
            "login": "test",
            "email": "test@test.com",
            "password": "test"
        }, web_session_id="user-session-id")


@get_api
def test_create_user(api):
    """
    Создание пользователя под администратором с правильной сессией
    """

    data = api.call("User", 'create', data={
        "name": "Администратор",
        "login": "test",
        "email": "test@test.com",
        "password": "test"
    }, web_session_id=ADMIN_SESSION)

    assert isinstance(data, dict)
    assert data['name'] == "Администратор"
    assert data['login'] == "test"
    assert data['email'] == "test@test.com"
    assert data['password'] == 'test'


@get_api
def test_correct_login(api):
    """
    Аутентификация с корректным пользователем
    """
    new_session_id = 'session-id'
    result = api.call("Authentication", 'login',
                      login='administrator',
                      password='secret',
                      web_session_id=new_session_id)

    assert result is True

    # Теперь с этой сессией можно производить запросы
    data = api.call("Role",
                    'read',
                    web_session_id=new_session_id)

    data = list(data)
    assert len(data) > 0  # Какой-то список ролей

    # А со старой нельзя
    with pytest.raises(exc.Unauthorized):
        api.call("Role",
                 'read',
                 web_session_id=ADMIN_SESSION)


@get_api
def test_bad_password(api):
    """
    Аутентификация с некорректным паролем
    """

    with pytest.raises(exc.NotFound):
        api.call("Authentication", 'login',
                 login='administrator',
                 password='wrong-password',
                 web_session_id='new-session-id')


@get_api
def test_bad_login(api):
    """
    Аутентификация с некорректным пользователем
    """

    with pytest.raises(exc.NotFound):
        api.call("Authentication", 'login',
                 login='admin',
                 password='secret',
                 web_session_id='new-session-id')


@get_api
def test_incorrect_perm(api):
    """
    Исключение при некорректных правах
    """
    with pytest.raises(exc.Forbidden):
        api.call('User', 'get', web_session_id=USER_SESSION)


@get_api
def test_correct_user_perm(api):
    """
    Проверка корректных прав

    """
    data = api.call('User', 'read', web_session_id=USER_SESSION)
    data = list(data)
    assert len(data) > 0  # Не нулевой список пользователей


@get_api
def test_permissions_controller(api):
    """
    Получение списка контроллеров
    """
    data = api.call('PermissionController', 'read',
                    web_session_id=ADMIN_SESSION)
    data = list(item['controller'] for item in data)
    assert 'Authentication' in data
    assert 'User' in data
    assert 'Role' in data
    assert 'UserRole' in data
    assert 'RolePermission' in data  # например
    assert 'PermissionController' in data  # и сам тоже


@get_api
def test_permissions_actions(api):
    """
    Получение списка действий по контроллеру
    :param api:
    :return:
    """
    data = api.call('PermissionAction', 'read',
                    filter=[{'property': '_',
                             'operator': '_',
                             'value': 'UserRole'}],
                    web_session_id=ADMIN_SESSION)
    data = list(item['action'] for item in data)
    assert 'get' in data
    assert 'read' in data
    assert 'destroy' in data
    assert 'create' in data
    assert 'update' in data
