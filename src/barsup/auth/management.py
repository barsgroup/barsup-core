# coding: utf-8
"""Manage-команды для создания пользователей, ролей и связи между ними."""
from getpass import getpass


def create_user_role(session, user, role, user_role):
    """
    Команда для создания пользователя, роли и связи между ними

    :param session: Сессия для коммита транзакции
    :param user: Сервис для пользователей
    :param role: Сервис для ролей
    :param user_role: Сервис для связки ролей и пользователей
    :return:
    """
    def wrapper(user_name=None, email=None, login=None,
                password=None, role_name=None, is_super=None,
                **kwargs):

        session.bind.echo = False

        if user_name is None:
            user_name = input(
                'Введите username: '
            )
        if email is None:
            email = input(
                'Введите e-mail: '
            )
        if login is None:
            login = input(
                'Введите логин: '
            )
        if password is None:
            password = password or getpass(
                'Введите пароль: '
            )
        if role_name is None:
            role_name = role_name or input(
                'Введите название роли (default=""): '
            ) or ""

        user_id = user.create(**{
            'name': user_name,
            'email': email,
            'login': login,
            'password': password
        })['id']
        messages = ['Пользователь с id="{0}" создан.'.format(user_id)]
        if role_name:
            while is_super not in ['yes', 'no']:
                is_super = input(
                    'Права суперпользователя? ([yes/no], default="yes"): '
                ) or 'yes'

            role_id = role.create(**{
                'name': role_name,
                'is_super': is_super == 'yes'
            })['id']

            user_role.create(user_id=user_id, role_id=role_id)
            messages.append(
                'Роль с id="{0}" и привязкой к пользователю '
                'с id="{1}" создана.'.format(role_id, user_id))

        print('\n'.join(messages))
        session.commit()
        return True

    return wrapper
