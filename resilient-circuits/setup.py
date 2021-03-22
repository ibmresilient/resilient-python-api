#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

""" setup.py for resilient-circuits module """

from __future__ import print_function
import os
from setuptools import setup, find_packages
import sys
from os import path
import io

here = os.path.abspath(os.path.dirname(__file__))


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


with io.open(path.join(here, 'README.md'), encoding='utf-8') as f:
    readme_text = f.read()
    long_description = readme_text.replace('### Changelog', "### Recent Changes\n {}".format(gather_changes()))

setup(
    name='resilient_circuits',
    use_scm_version={"root": "../", "relative_to": __file__},
    setup_requires=['setuptools_scm'],
    url='https://developer.ibm.com/resilient',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Security',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    author='IBM Resilient',
    install_requires=[
        'stompest>=2.3.0',
        'requests>=2.6.0',
        'circuits',
        'pytz',
        'jinja2>=2.10.0',
        'pysocks',
        'filelock>=2.0.5',
        'watchdog>=0.9.0, <1.0.0; python_version < "3.6.0"',
        'watchdog>=0.9.0; python_version >= "3.6.0"',
        'resilient>=38.0.0'
    ],
    author_email='support@resilientsystems.com',
    description='Resilient Circuits Framework for Custom Integrations',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    include_package_data=True,
    platforms='any',
    entry_points={
        'console_scripts': ['res-action-test = resilient_circuits.bin.res_action_test:main',
                            'resilient-circuits = resilient_circuits.bin.resilient_circuits_cmd:main']
    }
)
