# coding: utf-8
"""Различные утилиты для auth"""
import hashlib


def to_md5_hash(value, salt='2Bq('):
    """Конвертация значения в md5+salt представление"""
    data = hashlib.md5((salt + value).encode())
    return data.hexdigest()
