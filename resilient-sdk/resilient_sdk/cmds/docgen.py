#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

""" TODO: implement docgen """

import logging
import os
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util import helpers as sdk_helpers
from resilient_sdk.util import package_file_helpers as package_helpers

# Get the same logger object that is used in app.py
LOG = logging.getLogger("resilient_sdk_log")

# JINJA Constants
USER_GUIDE_TEMPLATE_NAME = "user_guide_README.md.jinja2"
INSTALL_GUIDE_TEMPLATE_NAME = "install_guide_README.md.jinja2"

# Relative paths from with the package of files + directories used
PATH_SETUP_PY = "setup.py"
PATH_CUSTOMIZE_PY = os.path.join("util", "customize.py")
PATH_CONFIG_PY = os.path.join("util", "config.py")
PATH_DOC_DIR = "doc"
PATH_SCREENSHOTS = os.path.join(PATH_DOC_DIR, "screenshots")
PATH_INSTALL_GUIDE_README = "README.md"
# PATH_DEFAULT_INSTALL_GUIDE_README = pkg_resources.resource_filename("resilient_circuits", "data/template_package/README.md.jinja2")
PATH_USER_GUIDE_README = os.path.join(PATH_DOC_DIR, "README.md")
# PATH_DEFAULT_USER_GUIDE_README = pkg_resources.resource_filename("resilient_circuits", "data/template_package/doc/README.md.jinja2")


class CmdDocgen(BaseCmd):
    """TODO Docstring"""

    CMD_NAME = "docgen"
    CMD_HELP = "Generate documentation for an Extension"
    CMD_USAGE = """
    $ resilient-sdk docgen -p <path_to_package>
    $ resilient-sdk docgen -p <path_to_package> --only-user-guide
    $ resilient-sdk docgen -p <path_to_package> --only-install-guide"""
    CMD_DESCRIPTION = "Generate documentation for an Extension"

    def setup(self):
        # Define docgen usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        # Add any positional or optional arguments here
        self.parser.add_argument("-p",
                                 type=ensure_unicode,
                                 help="Path to the directory containing the setup.py file",
                                 nargs="?",
                                 default=os.getcwd())

        parser_group = self.parser.add_mutually_exclusive_group(required=False)

        parser_group.add_argument("--only-user-guide",
                                  help="Only generate the User Guide",
                                  action="store_true")

        parser_group.add_argument("--only-install-guide",
                                  help="Only generate the Install Guide",
                                  action="store_true")

    def execute_command(self, args):
        LOG.info("Called docgen with %s", args)

        # Get absolute path_to_src
        path_to_src = os.path.abspath(args.p)

        # Instansiate Jinja2 Environment with path to Jinja2 templates
        jinja_env = sdk_helpers.setup_jinja_env("data/docgen/templates")

        # Load the Jinja2 Templates
        user_guide_readme_template = jinja_env.get_template(USER_GUIDE_TEMPLATE_NAME)
        install_guide_readme_template = jinja_env.get_template(INSTALL_GUIDE_TEMPLATE_NAME)

        # Generate paths to required directories + files
        path_setup_py_file = os.path.join(path_to_src, PATH_SETUP_PY)
        path_customize_py_file = os.path.join(path_to_src, os.path.basename(path_to_src), PATH_CUSTOMIZE_PY)
        path_config_py_file = os.path.join(path_to_src, os.path.basename(path_to_src), PATH_CONFIG_PY)
        path_install_guide_readme = os.path.join(path_to_src, PATH_INSTALL_GUIDE_README)
        path_doc_dir = os.path.join(path_to_src, PATH_DOC_DIR)
        path_screenshots_dir = os.path.join(path_to_src, PATH_SCREENSHOTS)
        path_user_guide_readme = os.path.join(path_to_src, PATH_USER_GUIDE_README)

        # Ensure we have read permissions for each required file and the file exists
        sdk_helpers.validate_file_paths(os.R_OK, path_setup_py_file, path_customize_py_file, path_config_py_file)

        # Check doc directory exists, if not, create it
        if not os.path.isdir(path_doc_dir):
            os.makedirs(path_doc_dir)

        # Check doc/screenshots directory exists, if not, create it
        if not os.path.isdir(path_screenshots_dir):
            os.makedirs(path_screenshots_dir)

        # Parse the setup.py file
        setup_py_attributes = package_helpers.parse_setup_py(path_setup_py_file, package_helpers.SUPPORTED_SETUP_PY_ATTRIBUTE_NAMES)

        # Get the resilient_circuits dependency string from setup.py file
        res_circuits_dependency_str = package_helpers.get_dependency_from_install_requires_str(setup_py_attributes.get("install_requires"), "resilient_circuits")

        # Get ImportDefinition from customize.py
        customize_py_import_definition = package_helpers.get_import_definition_from_customize_py(path_customize_py_file)

        # Parse the app.configs from the config.py file
        jinja_app_configs = package_helpers.get_configs_from_config_py(path_config_py_file)

        LOG.info("here")