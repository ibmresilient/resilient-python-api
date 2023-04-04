#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

""" Implemention of 'resilient-sdk init' """

import logging
import os

from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util import constants
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util.resilient_objects import (IGNORED_INCIDENT_FIELDS,
                                                  ResilientObjMap)
from resilient_sdk.util.sdk_exception import SDKException

# Get the same logger object that is used in app.py
LOG = logging.getLogger(constants.LOGGER_NAME)

class CmdRunInit(BaseCmd):
    """
    Create a sdk_settings.json file under ~/.resilient with default settings place
    for `codegen`, `docgen`, and `validate` commands
    """

    # TODO: add an option to provide path or to provide name?

    CMD_NAME = "init"
    CMD_HELP = "Generates sdk_settings.json to store default settings."
    CMD_USAGE = """
    $ resilient-sdk init
    """
    CMD_DESCRIPTION = CMD_HELP
    CMD_ADD_PARSERS = [constants.SDK_SETTINGS_PARSER_NAME]
    
    def setup(self):
        # Define init usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        # Add any positional or optional arguments here
        self.parser.add_argument("-f", "--file",
                                 type=ensure_unicode,
                                 required = False,
                                 help="Optional path to settings file.")
        
    def execute_command(self, args):
        LOG.debug(f"called: CmdRunInit.execute_command()")
        
        # If filename is provided in args, use that, otherwise use default .sdk_settings.json
        settings_file = args.file or constants.SDK_SETTINGS_FILE_PATH
        
        # Check the provided path
        settings_dir = os.path.dirname(settings_file)
        if not os.path.exists(settings_dir):
            LOG.info(f"Creating {settings_dir}")
            os.makedirs(settings_dir)
        
        overwrite = "y"
        # Check if the settings_file exists, if it does, prompt if we should overwrite
        if os.path.exists(settings_file):
            overwrite = input(f"{settings_file} exists already. Would you like to overwrite (y/n)? ")
        
        if overwrite.lower() == "n":
            # TODO: Why does this get printed to console?
            LOG.info(f"Will not overwrite {settings_file}... Exiting CmdRunInit.exeucte_command().")
            return
        
        # Instansiate Jinja2 Environment with path to Jinja2 templates
        jinja_env = sdk_helpers.setup_jinja_env(constants.SETTINGS_TEMPLATE_PATH)

        # Load the Jinja2 Template
        settings_template = jinja_env.get_template(constants.SETTINGS_TEMPLATE_NAME)

        rendered_settings = settings_template.render()

        LOG.info(f"Writing settings to: {settings_file}")

        # Write the new README
        sdk_helpers.write_file(settings_file, rendered_settings)

        return