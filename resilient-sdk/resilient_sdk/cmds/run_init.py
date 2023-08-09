#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

""" Implementation of 'resilient-sdk init' """

import logging
import os
import sys

from argparse import SUPPRESS
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util import constants
from resilient_sdk.util import sdk_helpers

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

        # Create an argument for internal use to skip the input field
        self.parser.add_argument("--no-input",
                                action='store_true',
                                required=False,
                                help=SUPPRESS)

    def execute_command(self, args):

        LOG.debug("called: CmdRunInit.execute_command()")

        # If filename is provided in args, use that, otherwise use default .sdk_settings.json
        settings_file = args.file or constants.SDK_SETTINGS_FILE_PATH

        # Check the provided path
        settings_dir = os.path.dirname(settings_file)
        if not os.path.exists(settings_dir):
            LOG.info("{} does not exist... Creating.".format(settings_dir))
            os.makedirs(settings_dir)

        overwrite = "y"
        # Check if the settings_file exists, if it does, prompt if we should overwrite
        # If --no-input is used, we should skip the prompt
        if os.path.exists(settings_file) and not args.no_input:
            if sys.version_info.major < 3:
                overwrite = raw_input("{} exists already. Would you like to overwrite (y/n)? ".format(settings_file))    
            else:
                overwrite = input("{} exists already. Would you like to overwrite (y/n)? ".format(settings_file))

        if overwrite.lower() != "y":
            LOG.info("Will not overwrite {}... Exiting CmdRunInit.execute_command().".format(settings_file))
            return

        # Instantiate Jinja2 Environment with path to Jinja2 templates
        jinja_env = sdk_helpers.setup_jinja_env(constants.SETTINGS_TEMPLATE_PATH)

        # Load the Jinja2 Template
        settings_template = jinja_env.get_template(constants.SETTINGS_TEMPLATE_NAME)

        LOG.debug("Rendering settings file with provided args")
        rendered_settings = settings_template.render({
            "author": constants.INIT_INTERNAL_AUTHOR if args.internal else (args.author or constants.CODEGEN_DEFAULT_SETUP_PY_AUTHOR),
            "author_email": constants.INIT_INTERNAL_AUTHOR_EMAIL if args.internal else (args.author_email or constants.CODEGEN_DEFAULT_SETUP_PY_EMAIL),
            "url": constants.INIT_INTERNAL_URL if args.internal else (args.url or constants.CODEGEN_DEFAULT_SETUP_PY_URL),
            "license": constants.INIT_INTERNAL_LICENSE if args.internal else (args.license or constants.CODEGEN_DEFAULT_SETUP_PY_LICENSE),
            "supported_app": "true" if args.internal else "false",
            "long_description": constants.INIT_INTERNAL_LONG_DESC if args.internal else constants.CODEGEN_DEFAULT_SETUP_PY_LONG_DESC,
            "license_content": constants.INIT_INTERNAL_LICENSE_CONTENT if args.internal else constants.CODEGEN_DEFAULT_LICENSE_CONTENT,
            "copyright": constants.INIT_INTERNAL_COPYRIGHT if args.internal else constants.CODEGEN_DEFAULT_COPYRIGHT_CONTENT
        })

        LOG.info("Writing settings to: {}".format(settings_file))

        # Write the new settings.json
        sdk_helpers.write_file(settings_file, rendered_settings)
