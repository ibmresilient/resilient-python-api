#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.
# pylint: disable=line-too-long

""" Python Module that exposes the ExtPackage class """

import logging
import os
from setuptools import sandbox as use_setuptools
from resilient_circuits.util.ext.ExtCreate import ExtCreate

# Get the same logger object that is used in resilient_circuits_cmd.py
LOG = logging.getLogger("resilient_circuits_cmd_logger")

# Constants
BASE_NAME_SETUP_PY = "setup.py"
BASE_NAME_DIST_DIR = "dist"

PATH_CUSTOMIZE_PY = os.path.join("util", "customize.py")
PATH_CONFIG_PY = os.path.join("util", "config.py")

PATH_ICON_EXTENSION_LOGO = os.path.join("icons", "extension_logo.png")
PATH_ICON_COMPANY_LOGO = os.path.join("icons", "company_logo.png")


class ExtPackage(ExtCreate):
    """ ExtPackage is a subclass of ExtCreate. It exposes one
    method: package_extension() """

    @classmethod
    def package_extension(cls, path_to_src, custom_display_name=None, keep_build_dir=False):
        """ Function that creates The Extension.zip file from the give source path and returns
        the path to the new Extension.zip
        - path_to_src [String]: must include a setup.py, customize.py and config.py file.
        - custom_display_name [String]: will give the Extension that display name. Default: name from setup.py file
        - keep_build_dir [Boolean]: if True, dist/build/ will not be remove. Default: False
        - The code will be packaged into a Built Distribution (.tar.gz) in the /dist directory
        - The Extension.zip will also be produced in the /dist directory"""

        # Ensure the src directory exists and we have WRITE access
        cls.__validate_directory__(os.W_OK, path_to_src)

        # Generate paths to files required to create extension
        path_setup_py_file = os.path.join(path_to_src, BASE_NAME_SETUP_PY)
        path_customize_py_file = os.path.join(path_to_src, os.path.basename(path_to_src), PATH_CUSTOMIZE_PY)
        path_config_py_file = os.path.join(path_to_src, os.path.basename(path_to_src), PATH_CONFIG_PY)
        path_output_dir = os.path.join(path_to_src, BASE_NAME_DIST_DIR)
        path_extension_logo = os.path.join(path_to_src, PATH_ICON_EXTENSION_LOGO)
        path_company_logo = os.path.join(path_to_src, PATH_ICON_COMPANY_LOGO)

        LOG.info("Creating Built Distribution in /dist directory")

        # Create the built distribution
        use_setuptools.run_setup(setup_script=path_setup_py_file, args=["sdist", "--formats=gztar"])

        LOG.info("Built Distribution (.tar.gz) created at: %s", path_output_dir)

        # Create the extension
        path_the_extension_zip = cls.create_extension(
            path_setup_py_file=path_setup_py_file,
            path_customize_py_file=path_customize_py_file,
            path_config_py_file=path_config_py_file,
            output_dir=path_output_dir,
            custom_display_name=custom_display_name,
            keep_build_dir=keep_build_dir,
            path_extension_logo=path_extension_logo,
            path_company_logo=path_company_logo
        )

        LOG.info("Extension created at: %s", path_the_extension_zip)

        return path_the_extension_zip
