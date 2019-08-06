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

    def setup(self):
        # Define docgen usage and description
        self.parser.usage = "resilient-sdk docgen -p <path_to_package>"
        self.parser.description = "Generate documentation for an Extension"

        # Add any positional or optional arguments here
        self.parser.add_argument("-p", "--package",
                                 metavar="",
                                 help="Path to package")

    def execute_command(self, args):
        LOG.info("Called docgen with %s", args)
