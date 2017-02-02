from setuptools import setup

requirements = [
    'pytest>=3.0.0',
]

setup(
    name='pytest_resilient_circuits',
    version='27.0.0',
    description='Resilient Circuits fixtures for Pytest.',
    author='IBM Resilient',
    license='Resilient License',
    url='https://www.resilientsystems.com/',
    author_email='support@resilientsystems.com',
    packages=['pytest_resilient_circuits'],
    install_requires=requirements,
    include_package_data=True,
    data_files = [("", ["LICENSE"])],
    entry_points={
        'pytest11': [
            'pytest_resilient_circuits = pytest_resilient_circuits.plugin'
        ]},
)
