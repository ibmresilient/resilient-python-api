#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

""" Implementation of `resilient-sdk ext:convert` """

import logging
import os
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util import sdk_helpers

# Get the same logger object that is used in app.py
LOG = logging.getLogger("resilient_sdk_log")


class CmdExtConvert(BaseCmd):
    """TODO Docstring"""

    CMD_NAME = "ext:convert"
    CMD_HELP = "Convert an old (built) Integration that can be in .tar.gz or .zip format into a Resilient Extension"
    CMD_USAGE = """
    $ resilient-sdk ext:convert TODO....
    """
    CMD_DESCRIPTION = "Convert an old (built) Integration that can be in .tar.gz or .zip format into a Resilient Extension"

    def setup(self):
        # Define codegen usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        # Add any positional or optional arguments here
        self.parser.add_argument("-p", "--package",
                                 type=ensure_unicode,
                                 help="(required) Path to the (old) Integration that can be in .tar.gz or .zip format",
                                 required=True)

        self.parser.add_argument("--display-name",
                                 help="The Display Name to give the Extension",
                                 nargs="?")

    def execute_command(self, args):
        LOG.debug("called: CmdExtPackage.execute_command()")
