#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

""" setup.py for resilient-lib Python Module """

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
    name="resilient_lib",
    use_scm_version={"root": "../", "relative_to": __file__},
    setup_requires=[
        "setuptools_scm < 6.0.0;python_version<'3.6'",
        "setuptools_scm >= 6.0.0;python_version>='3.6'"
    ],
    license="MIT",
    packages=find_packages(),
    include_package_data=True,

    # Runtime Dependencies
    install_requires=[
        # Our libraries
        "resilient      >= 45.0",

        # 3rd party dependencies for all python versions
        "pytz           ~= 2022.1",
        "deprecated     ~= 1.2",
        "beautifulsoup4 ~= 4.9",

        # Python >= 3.6
        "jinja2         ~= 3.0; python_version >= '3.6'",

        # Python 2.7
        "jinja2         ~= 2.0; python_version == '2.7'",
    ],

    # restrict supported python versions
    python_requires=_python_requires,

    entry_points={
        "resilient.lib.configsection": ["gen_config = resilient_lib.util.config:config_section_data"]
    },

    # PyPI metadata
    author="IBM SOAR",
    description="Contains common library calls which facilitate the development of Apps for IBM SOAR",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ibmresilient/resilient-python-api/tree/master/resilient-lib",
    project_urls={
        "API Docs": "https://ibm.biz/soar-python-docs",
        "IBM Community": "https://ibm.biz/soarcommunity",
        "Change Log": "https://ibm.biz/resilient-lib-changes"
    },
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.9"
    ],
    keywords="ibm soar resilient circuits lib resilient-lib common"

)
