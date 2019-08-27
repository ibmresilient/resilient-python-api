#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

""" TODO: implement docgen """

import logging
from resilient_sdk.cmds.base_cmd import BaseCmd

# Get the same logger object that is used in app.py
LOG = logging.getLogger("resilient_sdk_log")


class CmdDocgen(BaseCmd):
    """TODO Docstring"""

    CMD_NAME = "docgen"
    CMD_HELP = "TODO: docgen help message"
    CMD_USAGE = "resilient-sdk docgen -p <path_to_package>"
    CMD_DESCRIPTION = "Generate documentation for an Extension"

    def __init__(self, sub_parser):
        super(CmdDocgen, self).__init__(self.CMD_NAME, self.CMD_HELP, sub_parser)

    def setup(self):
        # Define docgen usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        # Add any positional or optional arguments here
        self.parser.add_argument("-p", "--package",
                                 metavar="",
                                 help="Path to package")

    def execute_command(self, args):
        LOG.info("Called docgen with %s", args)
