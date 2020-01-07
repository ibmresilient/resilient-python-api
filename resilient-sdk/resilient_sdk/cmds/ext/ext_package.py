#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

""" Implementation of `resilient-sdk ext:package` """

import logging
import os
from setuptools import sandbox as use_setuptools
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util.package_file_helpers import create_extension

# Get the same logger object that is used in app.py
LOG = logging.getLogger("resilient_sdk_log")

# Constants
BASE_NAME_SETUP_PY = "setup.py"
BASE_NAME_DIST_DIR = "dist"

PATH_CUSTOMIZE_PY = os.path.join("util", "customize.py")
PATH_CONFIG_PY = os.path.join("util", "config.py")

PATH_ICON_EXTENSION_LOGO = os.path.join("icons", "extension_logo.png")
PATH_ICON_COMPANY_LOGO = os.path.join("icons", "company_logo.png")


class CmdExtPackage(BaseCmd):
    """TODO Docstring"""

    CMD_NAME = "ext:package"
    CMD_HELP = "Package an Integration into a Resilient Extension"
    CMD_USAGE = """
    $ resilient-sdk ext:package TODO....
    """
    CMD_DESCRIPTION = "Package an Integration into a Resilient Extension"

    def setup(self):
        # Define codegen usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        # Add any positional or optional arguments here
        self.parser.add_argument("-p", "--package",
                                 type=ensure_unicode,
                                 help="(required) Path to the directory containing the setup.py file",
                                 required=True,
                                 default=os.getcwd())

        self.parser.add_argument("--keep-build-dir",
                                 help="Do not delete the dist/build directory",
                                 action="store_true")

        self.parser.add_argument("--display-name",
                                 help="The Display Name to give the Extension",
                                 nargs="?")

    def execute_command(self, args):
        """
        TODO: update this docstdring
        Function that creates The Extension.zip file from the give source path and returns
        the path to the new Extension.zip
        - path_to_src [String]: must include a setup.py, customize.py and config.py file.
        - custom_display_name [String]: will give the Extension that display name. Default: name from setup.py file
        - keep_build_dir [Boolean]: if True, dist/build/ will not be remove. Default: False
        - The code will be packaged into a Built Distribution (.tar.gz) in the /dist directory
        - The Extension.zip will also be produced in the /dist directory
        """
        
        # Set name for SDKException
        SDKException.command_ran = self.CMD_NAME

        # Get absolute path_to_src
        path_to_src = os.path.abspath(args.package)

        LOG.debug("Path to project: %s", path_to_src)

        # Ensure the src directory exists and we have WRITE access
        sdk_helpers.validate_dir_paths(os.W_OK, path_to_src)

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
        path_the_extension_zip = create_extension(
            path_setup_py_file=path_setup_py_file,
            path_customize_py_file=path_customize_py_file,
            path_config_py_file=path_config_py_file,
            output_dir=path_output_dir,
            custom_display_name=args.display_name,
            keep_build_dir=args.keep_build_dir,
            path_extension_logo=path_extension_logo,
            path_company_logo=path_company_logo
        )

        LOG.info("Extension created at: %s", path_the_extension_zip)

        return path_the_extension_zip
