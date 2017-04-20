#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Setup for co3 module """

from __future__ import print_function
import io
import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

here = os.path.abspath(os.path.dirname(__file__))

major_minor_version = "28.0"

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

#
def read_version_number():
    path = os.path.join(os.path.dirname(__file__), "co3", "version.txt")
    with open(path) as f:
        ver = f.read()
    return ver.strip()

version = read_version_number()

long_description = read('README')


class PyTest(TestCommand):
    user_options = [('configfile=', 'c', "Resilient Config File for co3argparse"),
                    ('co3args=', 'a', "Resilient Optional Args for co3argparse"),
                    ('pytestargs=', 'p', "Pytest Optional Args")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.configfile = ""
        self.co3args = ""
        self.pytestargs = ""
        self.test_suite = True
        self.test_args = []

    def finalize_options(self):
        import shlex
        TestCommand.finalize_options(self)
        if self.configfile:
            self.test_args += ["--config-file=%s" % self.configfile]
        if self.co3args:
            self.test_args += ["--co3args=%s" % self.co3args]
        if self.pytestargs:
            self.test_args += shlex.split(self.pytestargs)

    def run_tests(self):
        # import here, because outside the eggs aren't loaded
        print("Running Tests with args: %s" % self.test_args)
        import pytest
        errno = pytest.main(args=self.test_args)
        sys.exit(errno)


setup(
    name='co3',
    version=version,
    url='https://www.resilientsystems.com/',
    license='IBM Resilient License',

    author='IBM Resilient',
    install_requires=[
        'argparse',
        'stomp.py>=4.0.12',
        'requests>=2.6.0',
        'requests-toolbelt>=0.6.0',
        'requests-mock>=1.2.0',
        'six',
        'cachetools'
    ],
    extras_require={
        ':python_version < "3.2"': [
            'configparser'
        ]
    },
    tests_require=["pytest", ],
    cmdclass={"test": PyTest},
    author_email='support@resilientsystems.com',
    description='Resilient API',
    long_description=long_description,
    packages=find_packages(), # packages=['co3'],
    include_package_data=True,
    platforms='any',
    classifiers=[
        'Programming Language :: Python',
    ],
    entry_points={
        'console_scripts': ['finfo = co3.bin.finfo:main',
                            'gadget = co3.bin.gadget:main']
    }
)
