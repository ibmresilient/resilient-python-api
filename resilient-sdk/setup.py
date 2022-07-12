#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

""" setup.py for resilient-sdk Python Module """

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
    name="resilient_sdk",
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
        # Our libraries
        "resilient >= 45.0",

        # 3rd party dependencies for all python versions
        "genson    ~= 1.2",

        # Python >= 3.6
        "jinja2    ~= 3.0; python_version >= '3.6'",

        # Python 2.7
        "jinja2    ~= 2.0; python_version == '2.7'",
    ],

    # restrict supported python versions
    python_requires=_python_requires,

    # Add command line: resilient-sdk
    entry_points={
        "console_scripts": ["resilient-sdk=resilient_sdk.app:main"]
    },

    # PyPI metadata
    author="IBM SOAR",
    description="Python SDK for developing Apps for IBM SOAR",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ibmresilient/resilient-python-api/tree/master/resilient-sdk",
    project_urls={
        "IBM Community": "https://ibm.biz/soarcommunity",
        "Documentation": "https://ibm.biz/soar-python-docs",
        "Change Log": "https://ibm.biz/resilient-sdk-changes"
    },
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.9"
    ],
    keywords="ibm soar resilient circuits sdk resilient-sdk"
)
