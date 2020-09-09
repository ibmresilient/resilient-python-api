#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.

""" Setup for resilient module """

from __future__ import print_function
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from pkg_resources import get_distribution, DistributionNotFound
from os import path
import io

try:
    # pip version 10 onward
    from pip._internal.utils.misc import get_installed_distributions
except ImportError:
    from pip import get_installed_distributions


def check_deps():
    # Fail if the 'co3' module is installed, this supersedes it
    packages = get_installed_distributions(local_only=True)
    # For each EggInfoDistribution, find its metadata
    for pkg in packages:
        try:
            distro = get_distribution(pkg.project_name)
            if distro.project_name == 'co3':
                print("This package replaces the 'co3' distribution.  Please 'pip uninstall co3' first.")
                sys.exit(1)
        except DistributionNotFound:
            pass


if __name__ == "__main__":
    check_deps()


class PyTest(TestCommand):
    user_options = [('configfile=', 'c', "Resilient Config File for co3argparse"),
                    ('co3args=', 'a', "Resilient Optional Args for co3argparse"),
                    ('pytestargs=', 'p', "Pytest Optional Args")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.configfile = ""
        self.co3args = ""
        self.pytestargs = ""
        self.test_suite = True
        self.test_args = []

    def finalize_options(self):
        import shlex
        TestCommand.finalize_options(self)
        if self.configfile:
            self.test_args += ["--config-file=%s" % self.configfile]
        if self.co3args:
            self.test_args += ["--co3args=%s" % self.co3args]
        if self.pytestargs:
            self.test_args += shlex.split(self.pytestargs)

    def run_tests(self):
        # import here, because outside the eggs aren't loaded
        print("Running Tests with args: %s" % self.test_args)
        import pytest
        errno = pytest.main(args=self.test_args)
        sys.exit(errno)


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
    name='resilient',
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
        'argparse',
        'requests>=2.6.0',
        'requests-toolbelt>=0.6.0',
        'requests-mock>=1.2.0',
        'six',
        'cachetools<3.0.0',
        'setuptools>=41.0.0,!=50.0'
    ],
    extras_require={
        ':python_version < "3.2"': [
            'configparser'
        ],
        ':python_version >= "3.5"': [
            'keyring'
        ],
        ':python_version < "3.5"': [
            'keyring>=5.4,<19.0.0'
        ]
    },
    tests_require=["pytest>=3.0.0, <4.1.0", ],
    cmdclass={"test": PyTest},
    author_email='support@resilientsystems.com',
    description='Resilient API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    include_package_data=True,
    platforms='any',
    entry_points={
        'console_scripts': ['finfo = resilient.bin.finfo:main',
                            'gadget = resilient.bin.gadget:main',
                            'res-keyring = resilient.bin.res_keyring:main']
    }
)
