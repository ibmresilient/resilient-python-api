#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

""" setup.py for resilient-circuits Python module """

import io
from os import path

from setuptools import find_packages, setup

this_directory = path.abspath(path.dirname(__file__))

with io.open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="resilient_circuits",
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
        "stompest>=2.3.0",
        "circuits",
        "pytz",
        "jinja2 ~= 2.0;python_version<'3.6'",
        "jinja2 ~= 3.0;python_version>='3.6'",
        "pysocks",
        "filelock>=2.0.5",
        "watchdog>=0.9.0, <1.0.0; python_version < '3.6.0'",
        "watchdog>=0.9.0; python_version >= '3.6.0'",
        "resilient>=43.1.0",
        "resilient-lib>=43.0.0"
    ],

    entry_points={
        "console_scripts": ["res-action-test = resilient_circuits.bin.res_action_test:main",
                            "resilient-circuits = resilient_circuits.bin.resilient_circuits_cmd:main"]
    },

    # PyPI metadata
    author="IBM SOAR",
    description="Framework used to run IBM SOAR Apps and Integrations.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ibmresilient/resilient-python-api/tree/master/resilient-circuits",
    project_urls={
        "Documentation": "https://ibm.biz/soar-docs",
        "API Docs": "https://ibm.biz/soar-python-docs",
        "IBM Community": "https://ibm.biz/soarcommunity",
        "Change Log": "https://ibm.biz/resilient-circuits-changes"
    },
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.9"
    ],
    keywords="ibm soar resilient circuits resilient-circuits"
)
