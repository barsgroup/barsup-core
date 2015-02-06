# -*- coding: utf-8 -*-
"""Ключевые характеристики для сборки пакета."""

import os

from setuptools import setup, find_packages


def read(fname):
    """
    Получение текстового представления файла.

    :param fname:  Наименование файла
    :return: Текстовое представление
    """
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return ''

requires = []
with open('REQUIREMENTS', 'r') as f:
    requires.extend(f.readlines())

setup(
    name="barsup-core",
    version="0.2.6",
    license='MIT',
    description=read('DESCRIPTION'),
    author="Telepenin Nikolay, Aleksey Pirogov",
    author_email="telepenin@bars-open.ru,pirogov@bars-open.ru",
    url="https://bitbucket.org/barsgroup/barsup-core",
    classifiers=[
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'Natural Language :: Russian',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    long_description=read('README.rst'),
    install_requires=requires,
    scripts=['scripts/bup_cli', 'scripts/bup_manage'],
)
