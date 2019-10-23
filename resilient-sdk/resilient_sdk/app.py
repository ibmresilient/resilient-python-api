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


def get_main_app_parser():
    """
    Creates the main 'entry point' parser for resilient-sdk.

    :return: Main App Parser
    :rtype: argparse.ArgumentParser
    """
    # Define main parser object
    parser = argparse.ArgumentParser(
        prog="resilient-sdk",
        description="Python SDK for developing Resilient Extensions",
        epilog="For support, please visit ibm.biz/resilientcommunity")

    # Add --verbose argument
    parser.add_argument("-v", "--verbose",
                        help="Set the log level to DEBUG",
                        action="store_true")

    return parser


def get_main_app_sub_parser(parent_parser):
    """
    Creates and adds a sub_parser to parent_parser.
    Returns the sub_parser

    :param parent_parser: Parser to add the sub_parser to
    :type parent_parser: argparse.ArgumentParser
    :return: Sub Parser
    :rtype: argparse.ArgumentParser
    """
    # Define sub_parser object, its dest is cmd
    sub_parser = parent_parser.add_subparsers(
        title="subcommands",
        description="one of these subcommands must be provided",
        metavar="",
        dest="cmd"
    )

    return sub_parser


def main():
    """
    Main entry point for resilient-sdk
    """

    # Get main parser object
    parser = get_main_app_parser()

    # Get sub_parser object, its dest is cmd
    sub_parser = get_main_app_sub_parser(parser)

    # Add any subcommands to main app parser here
    cmd_docgen = CmdDocgen(sub_parser)
    cmd_codegen = CmdCodegen(sub_parser)

    # Parse the arguments
    args = parser.parse_args()

    # If -v was specified, set the log level to DEBUG
    if args.verbose:
        LOG.setLevel(logging.DEBUG)
        LOG.debug("Logging set to DEBUG mode")

    # Handle what subcommand was called
    if args.cmd == cmd_docgen.CMD_NAME:
        cmd_docgen.execute_command(args)

    elif args.cmd == cmd_codegen.CMD_NAME:
        cmd_codegen.execute_command(args)


if __name__ == "__main__":
    main()
