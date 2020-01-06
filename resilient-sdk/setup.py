#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

""" setup.py for resilient-sdk Python Module """

from setuptools import setup, find_packages

setup(
    name="resilient_sdk",
    version="1.0.0",
    license="MIT",
    packages=find_packages(),

    # Installation Dependencies
    setup_requires=[],

    # Runtime Dependencies
    install_requires=[
        "resilient>=35.0.0",
        "jinja2>=2.10.0"
    ],

    include_package_data=True,

    # Add command line: resilient-sdk
    entry_points={
        "console_scripts": ["resilient-sdk=resilient_sdk.app:main"]
    },

    # PyPI metadata
    author="IBM Resilient",
    author_email="support@resilientsystems.com",
    description="Python SDK for developing Extensions for the IBM Resilient Platform",
    url="https://github.com/ibmresilient/resilient-python-api/tree/master/resilient-sdk",
    project_urls={
        "IBM Community": "http://ibm.biz/resilientcommunity",
        "GitHub": "https://github.com/ibmresilient/resilient-python-api/tree/master/resilient-sdk"
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
        "Programming Language :: Python :: 3",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="ibm resilient circuits sdk resilient-sdk",
)
