#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.

""" setup.py for resilient module """

import io
from os import path

from setuptools import find_packages, setup

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
        "argparse",
        "requests>=2.26.0",
        "requests-toolbelt>=0.6.0",
        "requests-mock>=1.2.0",
        "six",
        "cachetools<3.0.0",
        "setuptools~=44.0;python_version<'3.0'",
        "setuptools>=59.0.0;python_version>='3.0'"
    ],
    extras_require={
        ":python_version < '3.2'": [
            "configparser"
        ],
        ":python_version >= '3.5'": [
            "keyring"
        ],
        ":python_version < '3.5'": [
            "keyring>=5.4,<19.0.0"
        ]
    },

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
