#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

from os import path
import io

this_directory = path.abspath(path.dirname(__file__))

with io.open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='resilient_lib',
    use_scm_version={"root": "../", "relative_to": __file__},
    setup_requires=['setuptools_scm'],
    url='https://github.com/ibmresilient/resilient-circuits-packages',
    license='MIT',
    author='IBM Resilient',
    author_email='support@resilientsystems.com',
    description="library for resilient-circuits functions",
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'bs4',
        'resilient_circuits>=30.0.0',
        'six'
    ],
    packages=find_packages(),
    include_package_data=True,
    platforms='any',
    classifiers=[
        'Programming Language :: Python',
    ],
    tests_require=['pytest>=3.0.0, <4.1.0'],
    entry_points={
        "resilient.lib.configsection": ["gen_config = resilient_lib.util.config:config_section_data"]
    }
)