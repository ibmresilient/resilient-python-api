#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

""" Implementation of `resilient-sdk app:package` """

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

PATH_ICON_EXTENSION_LOGO = os.path.join("icons", "app_logo.png")
PATH_ICON_COMPANY_LOGO = os.path.join("icons", "company_logo.png")


class CmdExtPackage(BaseCmd):
    """TODO Docstring"""

    CMD_NAME = "app:package"
    CMD_HELP = "Package an integration into a Resilient app"
    CMD_USAGE = """
    $ resilient-sdk app:package -p <path_to_directory>
    $ resilient-sdk app:package -p <path_to_directory> --display_name "My Custom App"
    $ resilient-sdk app:package -p <path_to_directory> --keep-build-dir --display_name "My Custom App"
    """
    CMD_DESCRIPTION = CMD_HELP

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
                                 help="The Display Name to give the App",
                                 nargs="?")

    def execute_command(self, args):
        """
        Function that creates The App.zip file from the give source path and returns
        the path to the new App.zip

        :param args: Arguments from command line:

            -  **args.package**: path to directory that must include a setup.py, customize.py and config.py file.
            -  **args.cmd**: `app:package` in this case
            -  **args.display_name**: will give the App that display name. Default: name from setup.py file
            -  **args.keep_build_dir**: if defined, dist/build/ will not be removed.
        :type args: argparse Namespace

        :return: Path to new app.zip
        :rtype: str
        """
        # Set name for SDKException
        SDKException.command_ran = self.CMD_NAME

        # Get absolute path_to_src
        path_to_src = os.path.abspath(args.package)

        LOG.debug("Path to project: %s", path_to_src)

        # Ensure the src directory exists and we have WRITE access
        sdk_helpers.validate_dir_paths(os.W_OK, path_to_src)

        # Generate paths to files required to create app
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

        # Create the app
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

        LOG.info("App created at: %s", path_the_extension_zip)

        return path_the_extension_zip
