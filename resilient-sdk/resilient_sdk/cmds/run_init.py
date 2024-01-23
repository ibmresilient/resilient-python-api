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
    CMD_HELP = "Generates sdk_settings.json to store default settings and app.config."
    CMD_USAGE = """
    $ resilient-sdk init
    $ resilient-sdk init -sf/--settings_file <path to settings json>
    $ resilient-sdk init -sf/--settings_file <path to settings json> -a/--author you@example.com
    $ resilient-sdk init -cf/--config_file <path to app.config>
    """
    CMD_DESCRIPTION = CMD_HELP
    
    def setup(self):
        # Define init usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        # Argument to specify a filepath for sdk_settings.json
        self.parser.add_argument("-sf", "--settings_file",
                                 type=ensure_unicode,
                                 required=False,
                                 help="Optional path to settings file.")
        
        # Argument to specify a filepath for app.config
        self.parser.add_argument("-cf", "--config_file",
                            type=ensure_unicode,
                            required=False,
                            help="Optional path to app.config file.")
        
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
                                action='store_true',    # True by default
                                required=False,
                                help=SUPPRESS)    # Use SUPPRESS to avoid printing this arg when doing `init -h`

        # Create an argument for internal use to skip the input field
        self.parser.add_argument("--no-input",
                                action='store_true',    # True by default
                                required=False,
                                help=SUPPRESS)      # Use SUPPRESS to avoid printing this arg when doing `init -h`

    def execute_command(self, args):

        LOG.debug("called: CmdRunInit.execute_command()")

        # If filename is provided in args, use that, otherwise use default .sdk_settings.json
        LOG.info("Checking for settings file")
        settings_file = args.settings_file or constants.SDK_SETTINGS_FILE_PATH
        
        # Check the provided path
        settings_dir = os.path.dirname(settings_file)
        if not os.path.exists(settings_dir):
            LOG.info("{} does not exist... Creating.".format(settings_dir))
            os.makedirs(settings_dir)
        
        write_settings = self.check_overwrite(settings_file, args.no_input)

        if write_settings:
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

        LOG.info("Checking for config file")
        # If filename is provided in args, use that, otherwise use default app.config
        
        # TODO: is this too risky? User might overwrite app.config by default...?
        config_file = args.config_file or constants.PATH_RES_DEFAULT_APP_CONFIG
        
        # Check the provided path
        config_dir = os.path.dirname(config_file)
        if not os.path.exists(config_dir):
            LOG.info("{} does not exist... Creating.".format(config_dir))
            os.makedirs(config_dir)
        
        write_config = self.check_overwrite(config_file, args.no_input)

        if write_config:
            # Instantiate Jinja2 Environment with path to Jinja2 templates
            jinja_env = sdk_helpers.setup_jinja_env(constants.CONFIG_TEMPLATE_PATH)

            # Load the Jinja2 Template
            config_template = jinja_env.get_template(constants.CONFIG_TEMPLATE_NAME)

            LOG.debug("Rendering config file")
            rendered_config = config_template.render()

            LOG.info("Writing config to: {}".format(config_file))

            # Write the new settings.json
            sdk_helpers.write_file(config_file, rendered_config)


    @staticmethod
    def check_overwrite(filename, no_input):
        """ Check if the file we're looking for (settings file or config file) exists.
            If it does, prompt the user if we should overwrite.
            If --no-input is used, we should skip the prompt, this is passed into the function with the `no_input` param

            :param filename: name of file to check
            :type filename: str
            :param no_input: from args.no_input which allows us to skip the input prompts if desired
            :type no_input: bool
            
            :returns: True if we should overwrite, False if we should overwrite.
            :rtype: bool
        """

        default_overwrite = "y"
        # Check if the settings_file exists, if it does, prompt if we should overwrite
        # If --no-input is used, we should skip the prompt
        if os.path.exists(filename) and not no_input:
            if sys.version_info.major < 3:
                default_overwrite = raw_input("{} exists already. Would you like to overwrite (y/n)? ".format(filename))    
            else:
                default_overwrite = input("{} exists already. Would you like to overwrite (y/n)? ".format(filename))
        
        if default_overwrite.lower() != "y":
            LOG.info("Will not overwrite {}.".format(filename))
            return False
        
        return True
