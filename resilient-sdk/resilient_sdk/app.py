#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

""" TODO: module docstring """

import logging
import argparse
from resilient_sdk.cmds import CmdDocgen, CmdCodegen

# Setup logging
LOG = logging.getLogger("resilient_sdk_log")
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler())

# Define subcommands and their help messages
CMD_NAME_DOCGEN = "docgen"
CMD_HELP_DOCGEN = "TODO: docgen help message"

CMD_NAME_CODEGEN = "codegen"
CMD_HELP_CODEGEN = "TODO: codegen help message"


def main():
    """TODO Docsting"""

    # Define main parser object
    parser = argparse.ArgumentParser(
        prog="resilient-sdk",
        description="Python SDK for developing Resilient Extensions",
        epilog="For support, please visit ibm.biz/resilientcommunity"
    )

    # Add --verbose argument
    parser.add_argument("-v", "--verbose",
                        help="Set the log level to DEBUG",
                        action="store_true")

    # Define sub_parser object, its dest is cmd
    sub_parser = parser.add_subparsers(
        title="subcommands",
        description="one of these subcommands must be provided",
        metavar="",
        dest="cmd"
    )

    # Define all subcommands here
    cmd_docgen = CmdDocgen(CMD_NAME_DOCGEN, CMD_HELP_DOCGEN, sub_parser)
    cmd_codegen = CmdCodegen(CMD_NAME_CODEGEN, CMD_HELP_CODEGEN, sub_parser)

    # Parse the arguments
    args = parser.parse_args()
    LOG.info("args: %s", args)

    # If -v was specified, set the log level to DEBUG
    if args.verbose:
        LOG.setLevel(logging.DEBUG)
        LOG.debug("Logging set to DEBUG mode")

    # Handle what subcommand was called
    if args.cmd == CMD_NAME_DOCGEN:
        cmd_docgen.execute_command(args)

    elif args.cmd == CMD_NAME_CODEGEN:
        cmd_codegen.execute_command(args)

if __name__ == "__main__":
    main()
