from __future__ import print_function
from setuptools import setup, find_packages
import io
import codecs
import os
import sys

here = os.path.abspath(os.path.dirname(__file__))

major_minor_version = "28.0"

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

# Write the co3/version.py file to contain the calculated version number.
bldno = os.getenv("BUILD_NUMBER")

if not bldno:
  raise Exception("BUILD_NUMBER environment variable not specified")

version = "{}.{}".format(major_minor_version, bldno)

with open("co3/version.py", "w") as vf:
  vf.write("resilient_version_number = '{}'".format(version))

long_description = read('README')

setup(
    name='co3',
    version=version,
    url='https://www.resilientsystems.com/',
    license='IBM Resilient License',
    author='IBM Resilient',
    install_requires=[
        'argparse',
        'stomp.py>=4.0.12',
        'requests>=2.6.0',
        'requests-toolbelt>=0.6.0'
    ],
    extras_require={
        ':python_version < "3.2"': [
            'configparser'
        ]
    },
    author_email='support@resilientsystems.com',
    description='Resilient API',
    long_description=long_description,
    packages=['co3'],
    include_package_data=True,
    platforms='any',
    data_files=[("", ["LICENSE"])],
    classifiers=[
        'Programming Language :: Python',
        ]
)
