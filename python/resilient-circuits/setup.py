#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from setuptools import setup, find_packages
import io
import os

here = os.path.abspath(os.path.dirname(__file__))


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

# Pull the version number from the version.txt file.
#
def read_version_number():
    path = os.path.join(os.path.dirname(__file__), "resilient_circuits", "version.txt")
    with open(path) as f:
        ver = f.read()
    return ver.strip()

version = read_version_number()

long_description = read('README')

setup(
    name='resilient_circuits',
    version=version,
    url='https://www.resilientsystems.com/',
    license='IBM Resilient License',

    author='IBM Resilient',
    install_requires=[
        'stomp.py>=4.0.12',
        'requests>=2.6.0',
        'circuits',
        'pytz',
        'jinja2',
        'filelock>=2.0.5',
        'co3>={}'.format(version)
    ],
    extras_require={
        ':"Debian" in platform_version': [
            'keyring<=9.1'  # There is no 'gcc' on Resilient appliance; later versions cause trouble
        ],
        ':python_version >= "2.7"': [
            'keyring'
        ],
        ':python_version == "2.6"': [
            'keyring==5.4'
        ]
    },
    author_email='support@resilientsystems.com',
    description='Resilient Circuits Framework for Custom Apps',
    long_description=long_description,
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
