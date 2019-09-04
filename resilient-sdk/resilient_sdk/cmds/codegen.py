#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

""" TODO: implement codegen """

import logging
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util.helpers import get_resilient_client

# Get the same logger object that is used in app.py
LOG = logging.getLogger("resilient_sdk_log")


class CmdCodegen(BaseCmd):
    """TODO Docstring"""

    CMD_NAME = "codegen"
    CMD_HELP = "TODO: codegen help message"
    CMD_USAGE = "resilient-sdk codegen -p <name_of_package> -m <message_destination>"
    CMD_DESCRIPTION = "Generate boilerplate code to start developing an Extension"
    CMD_USE_COMMON_PARSER_ARGS = True

    def setup(self):
        # Define codegen usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        # Add any positional or optional arguments here
        self.parser.add_argument("-p", "--package",
                                 type=ensure_unicode,
                                 help="Name of the package to generate")

        self.parser.add_argument("--reload",
                                 action="store_true",
                                 help="Reload customizations and create new customize.py")

    def execute_command(self, args):
        LOG.info("Called codegen command")

        # Instansiate connection to the Resilient Appliance
        res_client = get_resilient_client()

        if args.reload:
            self._reload_package(res_client, args)

        elif args.package:
            self._gen_package(res_client, args)

        elif not args.package and args.function:
            self._gen_function(res_client, args)

    @staticmethod
    def _gen_function(res_client, args):
        LOG.info("codegen _gen_function called")


    @staticmethod
    def _gen_package(res_client, args):
        LOG.info("codegen _gen_package called")

    @staticmethod
    def _reload_package(res_client, args):
        LOG.info("codegen _reload_package called")
