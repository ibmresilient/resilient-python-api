#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

""" Implemention of 'resilient-sdk init' """

import logging
import os
import shutil

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
        
    def execute_command(self, args):
        LOG.debug(f"called: CmdRunInit.execute_command()")
        # Use default config file in ~/.resilient/app.config.
        filename = ".sdk_settings_test.json"
        # settings_file = os.path.expanduser(os.path.join("~", ".resilient", filename))
        settings_file = constants.SDK_SETTINGS_FILE_PATH or args.path
        # If generating the config file location, create the '~/.resilient' directory if missing.
        resilient_dir = os.path.dirname(settings_file)
        if not os.path.exists(resilient_dir):
            LOG.info(f"Creating {resilient_dir}")
            os.makedirs(resilient_dir)
        
        # fill in the contents
        contents = '''{
            "validate":{
                "tox-args": {
                    "resilient_email": "test@example.org",
                    "resilient_password": "pwd_from_json_in_settings",
                    "resilient_host": "example.org",
                    "resilient_org": "example org from settings"
                },
                "pylint": [
                    "--enable=E,F"
                ],
                "bandit": [
                    "-ll"
                ]
            },
            "docgen":
                    {
                    "supported_app": true
            },
            "codegen":{
                    "setup": { 
                            "long_description": """example description"""
            },
            "license_content": "some text"
            }
        }\n'''

        sdk_helpers.write_file(settings_file, contents)
        pass