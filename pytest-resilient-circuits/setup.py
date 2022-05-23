#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.

""" Setup for pytest_resilient_circuits module """

import io
from os import path

from setuptools import find_packages, setup


# We only officially support 2.7, 3.6, 3.9. Following PEP 440
# this is the string format that allows for that restriction.
# This allows for >=3.6 but we recommend working with 3.9 or 3.6
_python_requires = ">=2.7," + ",".join("!=3.{0}.*".format(i) for i in range(6)) # note range() is non-inclusive of upper limit

this_directory = path.abspath(path.dirname(__file__))

with io.open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pytest_resilient_circuits',
    use_scm_version={"root": "../", "relative_to": __file__},
    setup_requires=[
        "setuptools_scm < 6.0.0;python_version<'3.0'",
        "setuptools_scm >= 6.0.0;python_version>='3.0'"
    ],

    packages=find_packages(),
    package_data={'pytest_resilient_circuits': ['version.txt']},
    include_package_data=True,

    # Runtime dependencies
    install_requires=[
        # Our libraries
        'resilient-circuits >= 45.0',

        # 3rd party dependencies for all python versions
        'requests-mock      ~= 1.9',

        # Python >= 3.6
        'ConfigParser       ~= 5.2; python_version >= "3.6"',
        'pytest             ~= 7.0; python_version >= "3.6"',

        # Python 2.7
        'ConfigParser       ~= 4.0; python_version == "2.7"',
        'pytest             ~= 4.6; python_version == "2.7"',
    ],

    # restrict supported python versions
    python_requires=_python_requires,

    entry_points={
        'pytest11': [
            'pytest_resilient_circuits = pytest_resilient_circuits.plugin'
        ]
    },

    # PyPI metadata
    author='IBM SOAR',
    description='Resilient Circuits fixtures for PyTest.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/ibmresilient/resilient-python-api/tree/master/pytest-resilient-circuits',
    project_urls={
        "Documentation": "https://ibm.biz/soar-docs",
        "API Docs": "https://ibm.biz/soar-python-docs",
        "IBM Community": "https://ibm.biz/soarcommunity"
    },
    license='MIT',
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.9"
    ],
    keywords="ibm soar pytest resilient circuits resilient-circuits"
)
