# coding: utf-8
"""Адаптеры для уровня auth"""

from barsup.auth.util import to_md5_hash


class Password:

    """ Адаптер, сохраняющий в базу вместо пароля md5+salt представление"""

    PASSWORD_FOR_READ = '***'

    def to_record(self, result, params):
        """См. barsup/adapter.py"""
        result.update(params)
        if 'password' in result:
            result['password'] = to_md5_hash(result['password'])
        return result, {}

    def from_record(self, result, params):
        """См. barsup/adapter.py"""
        result.update(params)
        if 'password' in result:
            result['password'] = self.PASSWORD_FOR_READ
        return result, {}
