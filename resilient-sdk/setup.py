#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

""" setup.py for resilient-sdk Python Module """

from os import path
import io
from setuptools import setup, find_packages

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
        "resilient>=42.0.0",
        "jinja2~=2.0",
        "setuptools>=44.0.0"
    ],

    # Add command line: resilient-sdk
    entry_points={
        "console_scripts": ["resilient-sdk=resilient_sdk.app:main"]
    },

    # PyPI metadata
    author="IBM SOAR",
    author_email="support@resilientsystems.com",
    description="Python SDK for developing Apps for the IBM SOAR (Resilient) Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ibmresilient/resilient-python-api/tree/master/resilient-sdk",
    project_urls={
        "IBM Community": "https://ibm.biz/soarcommunity",
        "GitHub": "https://github.com/ibmresilient/resilient-python-api/tree/master/resilient-sdk",
        "Change Log": "https://ibm.biz/resilient-sdk-changes"
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="ibm soar resilient circuits sdk resilient-sdk"
)
