from setuptools import setup
import os

# Pull the version number from the version.txt file.
#
def read_version_number():
    path = os.path.join(os.path.dirname(__file__), "pytest_resilient_circuits", "version.txt")
    with open(path) as f:
        ver = f.read()
    return ver.strip()

version = read_version_number()

major, minor, _ = version.split('.', 2)

requirements = [
    'pytest>=3.0.0',
    'co3>={}.{}'.format(major, minor),
    'resilient-circuits>={}.{}'.format(major, minor)
]

setup(
    name='pytest_resilient_circuits',
    version=version,
    description='Resilient Circuits fixtures for Pytest.',
    author='IBM Resilient',
    license='Resilient License',
    url='https://www.resilientsystems.com/',
    author_email='support@resilientsystems.com',
    packages=['pytest_resilient_circuits'],
    package_data={'pytest_resilient_circuits': ['version.txt']},
    install_requires=requirements,
    include_package_data=True,
    entry_points={
        'pytest11': [
            'pytest_resilient_circuits = pytest_resilient_circuits.plugin'
        ]},
)
