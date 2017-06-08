from __future__ import print_function

import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import os

# Pull the version number from the version.txt file.
#
def read_version_number():
    path = os.path.join(os.path.dirname(__file__), "file_lookup", "version.txt")
    with open(path) as f:
        ver = f.read()
    return ver.strip()

version = read_version_number()

major, minor, _ = version.split('.', 2)

class PyTest(TestCommand):
    user_options = [('pytestargs=', 'a', "Resilient Environment Arguments")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytestargs = []
        self.test_suite = True

    def finalize_options(self):
        import shlex
        TestCommand.finalize_options(self)
        self.test_args = ["-s",] + shlex.split(self.pytestargs)

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

setup(
    name='rc-file-lookup',
    version=version,
    url='https://www.resilientsystems.com/',
    license='Resilient License',
    author='IBM Resilient',
    install_requires=[
        'resilient_circuits>={}.{}'.format(major, minor)
    ],
    tests_require=["pytest",
                   "pytest_resilient_circuits"],
    cmdclass = {"test" : PyTest},
    author_email='support@resilientsystems.com',
    description="Resilient Circuits Component for Automatic CSV File Lookup",
    long_description = "Resilient Circuits Component for Automatic CSV File Lookup",
    packages=find_packages(),
    include_package_data=True,
    platforms='any',
    classifiers=[
        'Programming Language :: Python',
    ],
    entry_points={
        # Register the component with resilient_circuits
        "resilient.circuits.components": ["FileLookupComponent = file_lookup.components.file_lookup:FileLookupComponent"],
        "resilient.circuits.configsection": ["gen_config = file_lookup.components.file_lookup:config_section_data"]
    }
)
