#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

""" setup.py for resilient-circuits module """

from __future__ import print_function
import os
from setuptools import setup, find_packages
import sys
from os import path

here = os.path.abspath(os.path.dirname(__file__))

requires_resilient_version = "29.0"
major, minor = requires_resilient_version.split('.', 2)[:2]


if sys.version_info[0] == 2:
    import codecs

    with codecs.open(path.join(here, 'README.md'), 'r', encoding='utf8') as f:
        long_description = f.read()
else:
    with open(path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()

setup(
    name='resilient_circuits',
    use_scm_version={"root": "../", "relative_to": __file__},
    setup_requires=['setuptools_scm'],
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
        'jinja2>=2.10.0',
        'pysocks',
        'filelock>=2.0.5',
        'setuptools>=41.0.0',
        'resilient>={}.{}'.format(major, minor)
    ],
    author_email='support@resilientsystems.com',
    description='Resilient Circuits Framework for Custom Integrations',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    include_package_data=True,
    platforms='any',
    entry_points={
        'console_scripts': ['res-action-test = resilient_circuits.bin.res_action_test:main',
                            'resilient-circuits = resilient_circuits.bin.resilient_circuits_cmd:main']
    }
)
