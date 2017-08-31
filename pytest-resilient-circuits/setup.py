#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Setup for pytest_resilient_circuits module """

import os
from setuptools import setup


def read_version_number():
    """Pull the version number from the version.txt file."""
    path = os.path.join(os.path.dirname(__file__), "pytest_resilient_circuits", "version.txt")
    with open(path) as f:
        ver = f.read()
    return ver.strip()

version = read_version_number()

major, minor = version.split('.', 2)[:2]

requirements = [
    'pytest>=3.0.0',
    'resilient>={}.{}'.format(major, minor),
    'resilient-circuits>={}.{}'.format(major, minor)
]

setup(
    name='pytest_resilient_circuits',
    version=version,
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
