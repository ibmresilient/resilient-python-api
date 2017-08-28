#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" setup.py for resilient-circuits module """

from __future__ import print_function
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))


def read_version_number():
    """Pull the version number from the version.txt file."""
    path = os.path.join(os.path.dirname(__file__), "resilient_circuits", "version.txt")
    with open(path) as f:
        ver = f.read()
    return ver.strip()

version = read_version_number()

major, minor = version.split('.', 2)[:2]

setup(
    name='resilient_circuits',
    version=version,
    url='https://developer.ibm.com/resilient',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Security',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

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
    description='Resilient Circuits Framework for Custom Integrations',
    long_description='Resilient Circuits Framework for Custom Integrations',
    packages=find_packages(),
    include_package_data=True,
    platforms='any',
    entry_points={
        'console_scripts': ['res-action-test = resilient_circuits.bin.res_action_test:main',
                            'resilient-circuits = resilient_circuits.bin.resilient_circuits:main']
    }
)
