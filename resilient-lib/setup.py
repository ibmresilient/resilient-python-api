#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

from os import path
import io

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