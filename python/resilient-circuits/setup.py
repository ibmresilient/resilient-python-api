#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from setuptools import setup, find_packages
import io
import os

here = os.path.abspath(os.path.dirname(__file__))

# Pull the version number from the version.txt file.
#
def read_version_number():
    path = os.path.join(os.path.dirname(__file__), "resilient_circuits", "version.txt")
    with open(path) as f:
        ver = f.read()
    return ver.strip()

version = read_version_number()

major, minor = version.split('.', 2)[:2]

setup(
    name='resilient_circuits',
    version=version,
    url='https://www.resilientsystems.com/',
    license='IBM Resilient License',

    author='IBM Resilient',
    install_requires=[
        'stompest>=2.3.0',
        'requests>=2.6.0',
        'circuits',
        'pytz',
        'jinja2',
        'pysocks',
        'filelock>=2.0.5',
        'resilient>={}.{}'.format(major, minor)
    ],
    author_email='support@resilientsystems.com',
    description='Resilient Circuits Framework for Custom Apps',
    packages=find_packages(),
    include_package_data=True,
    platforms='any',
    classifiers=[
        'Programming Language :: Python',
    ],
    entry_points={
        'console_scripts': ['res-action-test = resilient_circuits.bin.res_action_test:main',
                            'resilient-circuits = resilient_circuits.bin.resilient_circuits:main']
    }
)
