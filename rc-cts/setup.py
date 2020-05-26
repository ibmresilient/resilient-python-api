from __future__ import print_function

import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

from os import path
import io



class PyTest(TestCommand):
    user_options = [('pytestargs=', 'a', "Resilient Environment Arguments")]
    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytestargs = ""
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

this_directory = path.abspath(path.dirname(__file__))
with io.open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    readme_text = f.read()
    long_description = readme_text


setup(
    name='rc-cts',
    setup_requires=['setuptools_scm'],
    use_scm_version={"root": "../", "relative_to": __file__},
    url='https://github.com/ibmresilient/resilient-circuits-packages',
    license='MIT',
    author='IBM Resilient',
    install_requires=[
        'resilient_circuits>=28.0.0',
        'rc-webserver'
    ],
    tests_require=["pytest",
                   "pytest_resilient_circuits"],
    cmdclass={"test": PyTest},
    author_email='support@resilientsystems.com',
    description="Resilient Circuits Custom Threat Service",
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    include_package_data=True,
    platforms='any',
    classifiers=[
        'Programming Language :: Python',
    ],
    entry_points={
        # Register the component with resilient_circuits
        "resilient.circuits.components": ["ThreatService = rc_cts.components.threat_webservice:CustomThreatService",
                                          "SearcherExample = rc_cts.components.searcher_example:SearcherExample"],
        "resilient.circuits.configsection": ["gen_config = rc_cts.components.threat_webservice:config_section_data"]
    }
)
