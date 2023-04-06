#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

""" Implemention of 'resilient-sdk init' """

import logging
import os

from argparse import SUPPRESS
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util import constants
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util.sdk_exception import SDKException

# Get the same logger object that is used in app.py
LOG = logging.getLogger(constants.LOGGER_NAME)

class CmdRunInit(BaseCmd):
    """
    Create a sdk_settings.json file under ~/.resilient with default settings place
    for `codegen`, `docgen`, and `validate` commands
    """

    CMD_NAME = "init"
    CMD_HELP = "Generates sdk_settings.json to store default settings."
    CMD_USAGE = """
    $ resilient-sdk init
    $ resilient-sdk init -f/--file <path to settings json>
    $ resilient-sdk init -f/--file <path to settings json> -a/--author you@example.com
    """
    CMD_DESCRIPTION = CMD_HELP
    CMD_ADD_PARSERS = [constants.SDK_SETTINGS_PARSER_NAME]
    
    def setup(self):
        # Define init usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        # Argument to specify a filepath
        self.parser.add_argument("-f", "--file",
                                 type=ensure_unicode,
                                 required=False,
                                 help="Optional path to settings file.")
        
        # Optional args for different fields in the settings file
        # TODO: Would it be better to allow something like this instead of individual arguments?
        ### $ resilient-sdk validate -p <name_of_package> --tests --tox-args resilient_password="secret_pwd" resilient_host="ibmsoar.example.com"
        self.parser.add_argument("-a", "--author",
                                 type=ensure_unicode,
                                 required=False,
                                 help="setup.py author name")
        self.parser.add_argument("-ae", "--author_email",
                                 type=ensure_unicode,
                                 required=False,
                                 help="setup.py author email")
        self.parser.add_argument("-u", "--url",
                                 type=ensure_unicode,
                                 required=False,
                                 help="setup.py company URL")
        self.parser.add_argument("-l", "--license",
                                type=ensure_unicode,
                                required=False,
                                help="setup.py license name")

        # Create an argument for internal use to pre-populate values
        self.parser.add_argument("-i", "--internal",
                                required=False,
                                action='store_true',
                                help=SUPPRESS)    # Use SUPPRESS to avoid printing this arg when doing `init -h`

    def execute_command(self, args):

        LOG.debug(f"called: CmdRunInit.execute_command()")
        
        # If filename is provided in args, use that, otherwise use default .sdk_settings.json
        settings_file = args.file or constants.SDK_SETTINGS_FILE_PATH
        
        # Check the provided path
        settings_dir = os.path.dirname(settings_file)
        if not os.path.exists(settings_dir):
            LOG.info(f"{settings_dir} does not exist... Creating.")
            os.makedirs(settings_dir)
        
        overwrite = "y"
        # Check if the settings_file exists, if it does, prompt if we should overwrite
        if os.path.exists(settings_file):
            overwrite = input(f"{settings_file} exists already. Would you like to overwrite (y/n)? ")
        
        if overwrite.lower() == "n":
            LOG.info(f"Will not overwrite {settings_file}... Exiting CmdRunInit.exeucte_command().")
            return
        
        # Instansiate Jinja2 Environment with path to Jinja2 templates
        jinja_env = sdk_helpers.setup_jinja_env(constants.SETTINGS_TEMPLATE_PATH)

        # Load the Jinja2 Template
        settings_template = jinja_env.get_template(constants.SETTINGS_TEMPLATE_NAME)

        LOG.debug("Rendering settings file with provided args")
        rendered_settings = settings_template.render({
            "author":  "IBM SOAR" if args.internal else (args.author or "<<your name here>>"),
            "author_email": "" if args.internal else (args.author_email or "you@example.com"),
            "url": "https://ibm.com/mysupport" if args.internal else (args.url or "<<your company url>>"),
            "license": "MIT" if args.internal else (args.license or "<<insert here>>"),
            "supported_app": "true" if args.internal else "false"
        })

        LOG.info(f"Writing settings to: {settings_file}")

        # Write the new settings.json
        sdk_helpers.write_file(settings_file, rendered_settings)

        return