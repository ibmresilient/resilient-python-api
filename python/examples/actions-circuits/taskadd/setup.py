from __future__ import print_function
from setuptools import setup, find_packages

setup(
    name='taskadd',
    version="27.0.0",
    url='https://www.resilientsystems.com/',
    license='Resilient License',
    author='IBM Resilient',
    install_requires=[
        'resilient_circuits>=27.1.0'
    ],
    author_email='support@resilientsystems.com',
    description="Resilient Circuits Component for Task Add Menu Item",
    long_description = "Resilient Circuits Component for Task Add Menu Item",
    packages=find_packages(),
    include_package_data=True,
    data_files = [("", ["LICENSE"])],
    platforms='any',
    classifiers=[
        'Programming Language :: Python',
    ],
    entry_points={
        # Register the component with resilient_circuits
        "resilient.circuits.components": ["AddTaskAction = taskadd.components.taskaddaction:AddTaskAction"]
    }
)
