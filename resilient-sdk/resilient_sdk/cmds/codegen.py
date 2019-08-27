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

    CMD_NAME = "codegen"
    CMD_HELP = "TODO: codegen help message"
    CMD_USAGE = "resilient-sdk codegen -p <name_of_package> -m <message_destination>"
    CMD_DESCRIPTION = "Generate boilerplate code to start developing an Extension"

    def __init__(self, sub_parser):
        super(CmdCodegen, self).__init__(self.CMD_NAME, self.CMD_HELP, sub_parser)

    def setup(self):
        # Define codegen usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

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
