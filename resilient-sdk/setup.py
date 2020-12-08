#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

""" setup.py for resilient-sdk Python Module """

from setuptools import setup, find_packages

from os import path
import io

this_directory = path.abspath(path.dirname(__file__))


def gather_changes():
    filepath = path.join(this_directory, "CHANGES")  # The file from which we will pull the changes
    with io.open(filepath) as fp:
        lines = fp.readlines()  # Take in all the lines as a list
        first_section = []
        for num, line in enumerate(lines, start=1):
            if "ver." in lines[num] and num != 0:
                # Get all the lines from the start of the list until num-1.
                # This, along with the if statement above will ensure we only capture the most recent change.
                first_section = lines[:num - 1]
                break
        # Return the section with a newline at the end
        return " \n ".join(first_section)


with io.open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    readme_text = f.read()
    long_description = readme_text.replace('<!-- [[pypi_changelog]] -->', "### Recent Changes\n {}".format(gather_changes()))


setup(
    name="resilient_sdk",
    use_scm_version={"root": "../", "relative_to": __file__},
    setup_requires=['setuptools_scm'],
    license="MIT",
    packages=find_packages(),

    # Runtime Dependencies
    install_requires=[
        "resilient>=36.2.0",
        "jinja2>=2.10.0",
        "setuptools>=44.0.0"
    ],

    include_package_data=True,

    # Add command line: resilient-sdk
    entry_points={
        "console_scripts": ["resilient-sdk=resilient_sdk.app:main"]
    },

    # PyPI metadata
    author="IBM Resilient",
    author_email="support@resilientsystems.com",
    description="Python SDK for developing Apps for the IBM Resilient Platform",
    long_description=long_description,
    long_description_content_type='text/markdown',
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
