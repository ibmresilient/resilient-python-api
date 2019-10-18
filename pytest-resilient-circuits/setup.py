#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.

""" Setup for pytest_resilient_circuits module """

import os
from setuptools import setup
import sys
from os import path

requires_resilient_version = "29.0"
major, minor = requires_resilient_version.split('.', 2)[:2]

requirements = [
    'pytest>=3.0.0, <4.1.0',
    'resilient>={}.{}'.format(major, minor),
    'resilient-circuits>={}.{}'.format(major, minor),
    'ConfigParser'
]

this_directory = path.abspath(path.dirname(__file__))

if sys.version_info[0] == 2:
    import codecs

    with codecs.open(path.join(this_directory, 'README.md'), 'r', encoding='utf8') as f:
        long_description = f.read()
else:
    with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()

setup(
    name='pytest_resilient_circuits',
    use_scm_version={"root": "../", "relative_to": __file__},
    setup_requires=['setuptools_scm'],
    url='https://developer.ibm.com/resilient',
    license='MIT',
    author='IBM Resilient',
    author_email='support@resilientsystems.com',
    description='Resilient Circuits fixtures for PyTest.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['pytest_resilient_circuits'],
    package_data={'pytest_resilient_circuits': ['version.txt']},
    install_requires=requirements,
    include_package_data=True,
    entry_points={
        'pytest11': [
            'pytest_resilient_circuits = pytest_resilient_circuits.plugin'
        ]},
)
