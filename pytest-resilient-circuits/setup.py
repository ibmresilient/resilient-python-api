#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.

""" Setup for pytest_resilient_circuits module """

import os
from setuptools import setup

version = "28.0"

major, minor = version.split('.', 2)[:2]

requirements = [
    'pytest>=3.0.0',
    'resilient>={}.{}'.format(major, minor),
    'resilient-circuits>={}.{}'.format(major, minor)
]

setup(
    name='pytest_resilient_circuits',
    use_scm_version={"root": "../", "relative_to": __file__},
    setup_requires=['setuptools_scm'],
    url='https://developer.ibm.com/resilient',
    license='MIT',
    author='IBM Resilient',
    author_email='support@resilientsystems.com',
    description='Resilient Circuits fixtures for PyTest.',
    packages=['pytest_resilient_circuits'],
    package_data={'pytest_resilient_circuits': ['version.txt']},
    install_requires=requirements,
    include_package_data=True,
    entry_points={
        'pytest11': [
            'pytest_resilient_circuits = pytest_resilient_circuits.plugin'
        ]},
)
