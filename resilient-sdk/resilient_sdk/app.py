#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

""" TODO: module docstring """

import logging
import os
import sys

from resilient_sdk.cmds import (CmdClone, CmdCodegen, CmdDev, CmdDocgen,
                                CmdExtPackage, CmdExtract, CmdValidate, CmdRunInit)
from resilient_sdk.util import constants, sdk_helpers, package_file_helpers
from resilient_sdk.util.sdk_argparse import SDKArgumentParser
from resilient_sdk.util.sdk_exception import SDKException

# Setup logging
LOG = logging.getLogger(constants.LOGGER_NAME)
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler())


def get_main_app_parser():
    """
    Creates the main 'entry point' parser for resilient-sdk.

    :return: Main App Parser
    :rtype: argparse.ArgumentParser
    """
    # Define main parser object
    # We use SDKArgumentParser which overwrites the 'error' method
    parser = SDKArgumentParser(
        prog=constants.SDK_PACKAGE_NAME,
        description="""Python SDK for developing IBM SOAR Apps that
        provides various subcommands to help with development""",
        epilog="For support, please visit https://ibm.biz/soarcommunity")

    parser.usage = """
    $ resilient-sdk <subcommand> ...
    $ resilient-sdk -v <subcommand> ...
    $ resilient-sdk codegen -p <name_of_package> -m 'fn_custom_md' -c '/usr/custom_app.config'
    $ resilient-sdk -h
    """

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

    pypi_warning = None

    # add color support for WINDOWS
    os.system("")

    # See if RES_SDK_DEV environment var is set
    sdk_dev = sdk_helpers.is_env_var_set(constants.ENV_VAR_DEV)

    # Check if we have latest version installed
    if sys.version_info.major >= 3:

        try:
            current_version = sdk_helpers.get_resilient_sdk_version()
            latest_available_version = sdk_helpers.get_latest_available_version()

            if current_version < latest_available_version:
                package_file_helpers.print_latest_version_warning(current_version, latest_available_version)

        except Exception as err:
            log_level = "WARNING"
            colored_lines = package_file_helpers.color_lines(log_level, [
                "{0}: Error getting latest version from PyPi:".format(log_level)
            ])
            pypi_warning = "{0}\n{1}\n\t{2}\n{0}".format(colored_lines[0], colored_lines[1], str(err))

    # Get main parser object
    parser = get_main_app_parser()

    # Get sub_parser object, its dest is cmd
    sub_parser = get_main_app_sub_parser(parser)

    if sdk_dev:
        # Add 'dev' command if environment var set
        cmd_dev = CmdDev(sub_parser)
        LOG.info("{0}Running SDK in Developer Mode{0}".format(constants.LOG_DIVIDER))
    else:
        cmd_dev = None

    # Add any subcommands to main app parser here
    cmd_validate = CmdValidate(sub_parser)
    cmd_codegen = CmdCodegen(sub_parser)
    cmd_clone = CmdClone(sub_parser)
    cmd_docgen = CmdDocgen(sub_parser)
    cmd_extract = CmdExtract(sub_parser)
    cmd_ext_package = CmdExtPackage(sub_parser, cmd_validate=cmd_validate)
    cmd_run_init = CmdRunInit(sub_parser)

    try:
        # Parse the arguments
        args = parser.parse_args()

        if args.cmd is None:
            parser.print_help()
            sys.exit()

    except SDKException as err:
        # Get main_cmd (codegen, docgen etc.)
        main_cmd = sdk_helpers.get_main_cmd()

        LOG.error(err)
        LOG.info("{0}".format(constants.LOG_DIVIDER))

        # Print specifc usage for that cmd for these errors
        if "too few arguments" in err.message or "no subcommand provided" in err.message:
            if main_cmd == cmd_codegen.CMD_NAME:
                cmd_codegen.parser.print_usage()

            elif main_cmd == cmd_clone.CMD_NAME:
                cmd_clone.parser.print_usage()

            elif main_cmd == cmd_docgen.CMD_NAME:
                cmd_docgen.parser.print_usage()

            elif main_cmd == cmd_extract.CMD_NAME:
                cmd_extract.parser.print_usage()

            elif main_cmd == cmd_ext_package.CMD_NAME:
                cmd_ext_package.parser.print_usage()

            elif main_cmd == cmd_validate.CMD_NAME:
                cmd_validate.parser.print_usage()

            elif sdk_dev and main_cmd == cmd_dev.CMD_NAME:
                cmd_dev.parser.print_usage()

            elif main_cmd == cmd_run_init.CMD_NAME:
                cmd_run_init.parser.print_usage()

            else:
                parser.print_help()

        # Exit
        sys.exit()

    # If -v was specified, set the log level to DEBUG
    if args.verbose:
        LOG.setLevel(logging.DEBUG)
        LOG.debug("Logging set to DEBUG mode")

        if pypi_warning:
            LOG.debug(pypi_warning)

    # Handle what subcommand was called
    if args.cmd == cmd_docgen.CMD_NAME:
        cmd_docgen.execute_command(args)

    elif args.cmd == cmd_codegen.CMD_NAME:
        cmd_codegen.execute_command(args)

    elif args.cmd == cmd_clone.CMD_NAME:
        cmd_clone.execute_command(args)

    elif args.cmd == cmd_extract.CMD_NAME:
        cmd_extract.execute_command(args)

    elif args.cmd == cmd_ext_package.CMD_NAME:
        cmd_ext_package.execute_command(args)

    elif args.cmd == cmd_validate.CMD_NAME:
        cmd_validate.execute_command(args)
    elif sdk_dev and args.cmd == cmd_dev.CMD_NAME:
        cmd_dev.execute_command(args)
    
    elif args.cmd == cmd_run_init.CMD_NAME:
        cmd_run_init.execute_command(args)


if __name__ == "__main__":
    main()
