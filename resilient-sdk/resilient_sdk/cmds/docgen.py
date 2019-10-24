#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

""" TODO: implement docgen """

import logging
import os
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd

# Get the same logger object that is used in app.py
LOG = logging.getLogger("resilient_sdk_log")


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
