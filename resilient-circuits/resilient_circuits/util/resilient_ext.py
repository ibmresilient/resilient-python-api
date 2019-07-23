#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.
# pylint: disable=line-too-long

"""Python Module to handle resilient-circuits ext: commands"""

import logging
import os
from resilient_circuits.util.ext import ExtPackage, ExtConvert, ExtException

# Get the same logger object that is used in resilient_circuits_cmd.py
LOG = logging.getLogger("resilient_circuits_cmd_logger")

SUPPORTED_EXT_COMMANDS = (
    "ext:package",
    "ext:convert")


def ext_command_handler(cmd, args):
    """Function that handles all resilient-circuits commands prefixed with 'ext:'"""

    # Handle if an unsupported command was called
    if cmd not in SUPPORTED_EXT_COMMANDS:
        raise ExtException("Unsupported command: {0}. Supported commands are: {1}".format(cmd, SUPPORTED_EXT_COMMANDS))

    path_to_src = None
    display_name = None
    keep_build_dir = False

    # Handle arguments
    if hasattr(args, "p"):
        path_to_src = os.path.abspath(args.p)

    if hasattr(args, "display_name"):
        display_name = args.display_name

    if hasattr(args, "keep_build_dir"):
        keep_build_dir = args.keep_build_dir

    LOG.debug("-----START ARGS DEBUG------")
    LOG.debug("args:\t\t\t%s", args)
    LOG.debug("path_to_src:\t\t%s", path_to_src)
    LOG.debug("display_name:\t\t%s", display_name)
    LOG.debug("keep_build_dir:\t\t%s", keep_build_dir)
    LOG.debug("-----END ARGS DEBUG-------")

    # Handle "ext:package"
    if cmd == SUPPORTED_EXT_COMMANDS[0]:
        ext_creator = ExtPackage(cmd)
        ext_creator.package_extension(path_to_src, custom_display_name=display_name, keep_build_dir=keep_build_dir)

    # Handle "ext:convert"
    elif cmd == SUPPORTED_EXT_COMMANDS[1]:
        ext_creator = ExtConvert(cmd)
        ext_creator.convert_to_extension(path_to_src, custom_display_name=display_name)
