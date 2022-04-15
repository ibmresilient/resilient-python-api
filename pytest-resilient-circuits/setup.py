#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.

""" Setup for pytest_resilient_circuits module """

import io
import os
from os import path

from setuptools import setup

this_directory = path.abspath(path.dirname(__file__))


def gather_changes():
    filepath = './CHANGES'  # The file from which we will pull the changes
    with io.open(filepath) as fp:
        lines = fp.readlines()  # Take in all the lines as a list
        first_section = []
        for num, line in enumerate(lines, start=1):
            if "version" in lines[num] and num != 0:
                # Get all the lines from the start of the list until num-1.
                # This, along with the if statement above will ensure we only capture the most recent change.
                first_section = lines[:num-1]
                break
        # Return the section with a newline at the end
        return " \n ".join(first_section)


with io.open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    readme_text = f.read()
    long_description = readme_text.replace('### Changelog', "### Recent Changes\n {}".format(gather_changes()))

setup(
    name='pytest_resilient_circuits',
    use_scm_version={"root": "../", "relative_to": __file__},
    setup_requires=[
        "setuptools_scm < 6.0.0;python_version<'3.0'",
        "setuptools_scm >= 6.0.0;python_version>='3.0'"
    ],
    url='https://developer.ibm.com/resilient',
    license='MIT',
    author='IBM Resilient',
    author_email='support@resilientsystems.com',
    description='Resilient Circuits fixtures for PyTest.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['pytest_resilient_circuits'],
    package_data={'pytest_resilient_circuits': ['version.txt']},
    install_requires=[
        # Our libraries
        'resilient-circuits >= 44.1',

        # 3rd party dependencies for all python versions
        'requests-mock ~= 1.9',

        # Python >= 3.6
        'ConfigParser ~= 5.2; python_version >= "3.6"',
        'pytest ~= 7.0; python_version >= "3.6"',

        # Python 2.7
        'ConfigParser ~= 4.0; python_version == "2.7"',
        'pytest ~= 4.6; python_version == "2.7"',
    ],
    include_package_data=True,
    entry_points={
        'pytest11': [
            'pytest_resilient_circuits = pytest_resilient_circuits.plugin'
        ]
    },
)
