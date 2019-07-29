#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import glob
import ntpath

def get_module_name(module_path):
    """
    Return the module name of the module path
    """
    return ntpath.split(module_path)[1].split(".")[0]

def snake_to_camel(word):
    """
    Convert a word from snake_case to CamelCase
    """
    return ''.join(x.capitalize() or '_' for x in word.split('_'))

setup(
    name='fn_mock_integration',
    version='1.0.0',
    license='MIT License',
    author='Example Author Name',
    author_email='aryastark@example.com',
    url='www.example.com',
    description="An example description for the purpose of unit tests",
    long_description="""Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do 
    eiusmod tempor incididunt ut labore et dolore magna aliqua. Mauris cursus mattis 
    molestie a iaculis. Cursus risus at ultrices mi tempus imperdiet nulla 
    malesuada pellentesque. Curabitur vitae nunc sed velit. Quis imperdiet massa 
    tincidunt nunc pulvinar sapien et. Morbi blandit cursus risus at ultrices mi 
    tempus imperdiet. Risus ultricies tristique nulla aliquet enim tortor at auctor urna""",
    install_requires=[
        'resilient_circuits>=30.0.0'
    ],
    packages=find_packages(),
    include_package_data=True,
    platforms='any',
    classifiers=[
        'Programming Language :: Python',
    ],
    entry_points={
        "resilient.circuits.components": [
            # When setup.py is executed, loop through the .py files in the components directory and create the entry points.
            "{}FunctionComponent = fn_mock_integration.components.{}:FunctionComponent".format(snake_to_camel(get_module_name(filename)), get_module_name(filename)) for filename in glob.glob("./fn_mock_integration/components/[a-zA-Z]*.py")
        ],
        "resilient.circuits.configsection": ["gen_config = fn_mock_integration.util.config:config_section_data"],
        "resilient.circuits.customize": ["customize = fn_mock_integration.util.customize:customization_data"],
        "resilient.circuits.selftest": ["selftest = fn_mock_integration.util.selftest:selftest_function"]
    }
)