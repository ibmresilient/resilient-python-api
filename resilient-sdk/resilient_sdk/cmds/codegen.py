#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

""" TODO: implement codegen """

import logging
from resilient_sdk.cmds.base_cmd import BaseCmd

# Get the same logger object that is used in app.py
LOG = logging.getLogger("resilient_sdk_log")


class CmdCodegen(BaseCmd):
    """TODO Docstring"""

    def setup(self):
        # Define codegen usage and description
        self.parser.usage = "resilient-sdk codegen -p <name_of_package> -m <message_destination>"
        self.parser.description = "Generate boilerplate code to start developing an Extension"

        # Add any positional or optional arguments here
        self.parser.add_argument("-p", "--package",
                                 metavar="",
                                 help="Name of package",
                                 required=True)

        self.parser.add_argument("-m", "--msg_dest",
                                 metavar="",
                                 help="Message Destination")

    def execute_command(self, args):
        LOG.info("Called codegen with %s", args)
