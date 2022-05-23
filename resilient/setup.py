#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.

""" setup.py for resilient module """

import io
from os import path

from setuptools import find_packages, setup


# We only officially support 2.7, 3.6, 3.9. Following PEP 440
# this is the string format that allows for that restriction.
# This allows for >=3.6 but we recommend working with 3.9 or 3.6
_python_requires = ">=2.7," + ",".join("!=3.{0}.*".format(i) for i in range(6)) # note range() is non-inclusive of upper limit

this_directory = path.abspath(path.dirname(__file__))

with io.open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="resilient",
    use_scm_version={"root": "../", "relative_to": __file__},
    setup_requires=[
        "setuptools_scm < 6.0.0;python_version<'3.0'",
        "setuptools_scm >= 6.0.0;python_version>='3.0'"
    ],
    license="MIT",
    packages=find_packages(),
    include_package_data=True,

    # Runtime Dependencies
    install_requires=[
        # General dependencies applicable to all python versions
        "requests          ~= 2.27",
        "requests-toolbelt ~= 0.9",
        "six               ~= 1.16",

        # Python > 3.6
        "setuptools        ~= 62.1;   python_version > '3.6'",
        "keyring           ~= 23.5;   python_version > '3.6'",
        "cachetools        ~= 5.0;    python_version > '3.6'",

        # Python 3.6
        "setuptools        ~= 59.6;   python_version == '3.6'",
        "keyring           ~= 23.4;   python_version == '3.6'",
        "cachetools        ~= 2.1;    python_version == '3.6'",

        # Python 2.7
        # configparser is only required for py 2.7 as it is packaged with python in > 3.2
        "configparser      ~= 4.0;    python_version == '2.7'", 
        "setuptools        ~= 44.0;   python_version == '2.7'",
        "cachetools        ~= 2.1;    python_version == '2.7'",
        "keyring           == 18.0.1; python_version == '2.7'",
    ],

    # restrict supported python versions
    python_requires=_python_requires,

    entry_points={
        "console_scripts": ["finfo = resilient.bin.finfo:main",
                            "gadget = resilient.bin.gadget:main",
                            "res-keyring = resilient.bin.res_keyring:main"]
    },

    # PyPI metadata
    author="IBM SOAR",
    description="Python client module for the IBM SOAR REST API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ibmresilient/resilient-python-api/tree/master/resilient",
    project_urls={
        "Documentation": "https://ibm.biz/soar-python-docs",
        "API Docs": "https://ibm.biz/soar-python-docs",
        "IBM Community": "https://ibm.biz/soarcommunity",
        "Change Log": "https://ibm.biz/resilient-changes"
    },
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.9"
    ],
    keywords="ibm soar resilient resilient-circuits circuits resilient-sdk sdk"
)
