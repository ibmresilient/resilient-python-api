#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

""" Implementation of `resilient-sdk package` """

import logging
import os
from setuptools import sandbox as use_setuptools
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util import package_file_helpers as package_helpers

# Get the same logger object that is used in app.py
LOG = logging.getLogger(sdk_helpers.LOGGER_NAME)


class CmdExtPackage(BaseCmd):
    """TODO Docstring"""

    CMD_NAME = "package"
    CMD_HELP = "Package an integration into a Resilient app"
    CMD_USAGE = """
    $ resilient-sdk package -p <path_to_directory>
    $ resilient-sdk package -p <path_to_directory> --display-name "My Custom App"
    $ resilient-sdk package -p <path_to_directory> --repository-name "ibmresilient"
    $ resilient-sdk package -p <path_to_directory> --keep-build-dir --display-name "My Custom App"
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
                                 help="Display name to give the app",
                                 nargs="?")

        self.parser.add_argument("--repository-name",
                                 help="Name of the repository which contains the app container",
                                 default="ibmresilient",
                                 nargs="?")

    def execute_command(self, args):
        """
        Function that creates The App.zip file from the give source path and returns
        the path to the new App.zip

        :param args: Arguments from command line:

            -  **args.package**: path to directory that must include a setup.py, customize.py and config.py file.
            -  **args.cmd**: `package` in this case
            -  **args.display_name**: will give the App that display name. Default: name from setup.py file
            -  **args.repository_name**: if defined, it will replace the default image repository name in app.json for
                                         container access.
            -  **args.keep_build_dir**: if defined, dist/build/ will not be removed.
        :type args: argparse Namespace

        :return: Path to new app.zip
        :rtype: str
        """
        # Set name for SDKException
        SDKException.command_ran = self.CMD_NAME

        # Get absolute path_to_src
        path_to_src = os.path.abspath(args.package)

        LOG.debug("\nPath to project: %s", path_to_src)

        # Ensure the src directory exists and we have WRITE access
        sdk_helpers.validate_dir_paths(os.W_OK, path_to_src)

        # Generate path to setup.py file
        path_setup_py_file = os.path.join(path_to_src, package_helpers.BASE_NAME_SETUP_PY)

        # Ensure we have read permissions for setup.py
        sdk_helpers.validate_file_paths(os.R_OK, path_setup_py_file)

        # Parse the setup.py file
        setup_py_attributes = package_helpers.parse_setup_py(path_setup_py_file, package_helpers.SUPPORTED_SETUP_PY_ATTRIBUTE_NAMES)

        LOG.debug("\nProject name: %s", setup_py_attributes.get("name", "unknown"))

        # Generate paths to files required to create app
        path_docker_file = os.path.join(path_to_src, package_helpers.BASE_NAME_DOCKER_FILE)
        path_entry_point = os.path.join(path_to_src, package_helpers.BASE_NAME_ENTRY_POINT)
        path_apikey_permissions_file = os.path.join(path_to_src, package_helpers.BASE_NAME_APIKEY_PERMS_FILE)
        path_output_dir = os.path.join(path_to_src, package_helpers.BASE_NAME_DIST_DIR)
        path_extension_logo = os.path.join(path_to_src, package_helpers.PATH_ICON_EXTENSION_LOGO)
        path_company_logo = os.path.join(path_to_src, package_helpers.PATH_ICON_COMPANY_LOGO)

        # Ensure the 'Dockerfile' and 'entrypoint.sh' files exist and we have READ access
        sdk_helpers.validate_file_paths(os.R_OK, path_docker_file, path_entry_point)

        LOG.info("\nBuilt Distribution starting\n")

        # Create the built distribution
        use_setuptools.run_setup(setup_script=path_setup_py_file, args=["sdist", "--formats=gztar"])

        LOG.info("\nBuilt Distribution finished. See: %s", path_output_dir)

        # Create the app
        path_the_extension_zip = package_helpers.create_extension(
            path_setup_py_file=path_setup_py_file,
            path_apikey_permissions_file=path_apikey_permissions_file,
            output_dir=path_output_dir,
            custom_display_name=args.display_name,
            repository_name=args.repository_name,
            keep_build_dir=args.keep_build_dir,
            path_extension_logo=path_extension_logo,
            path_company_logo=path_company_logo
        )

        LOG.info("App created at: %s", path_the_extension_zip)

        return path_the_extension_zip
