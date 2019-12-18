#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

import argparse
from resilient import ensure_unicode
from resilient_sdk.util.sdk_argparse import SDKArgHelpFormatter


class BaseCmd(object):
    """
    Base Class for implementing a resilient-sdk command e.g. codegen
    Sub classes must set/implement:
        -   CMD_NAME
        -   CMD_HELP
        -   setup(self)
        -   execute_comment(self, args)

    On initialization, it sets self.parser, then calls the sub-classes' setup method.
    This allows us to add custom command line args for each sub_command.
    See codegen.py for an example.
    """

    CMD_NAME = None
    CMD_HELP = None
    CMD_USAGE = None
    CMD_DESCRIPTION = None
    CMD_USE_COMMON_PARSER_ARGS = False  # Set this to True in sub class to include the common_parser arguments

    def __init__(self, sub_parser):

        assert self.CMD_NAME
        assert self.CMD_HELP

        if self.CMD_USE_COMMON_PARSER_ARGS:
            self.parser = sub_parser.add_parser(self.CMD_NAME,
                                                help=self.CMD_HELP,
                                                formatter_class=SDKArgHelpFormatter,
                                                parents=self._get_common_parser())
        else:
            self.parser = sub_parser.add_parser(self.CMD_NAME,
                                                help=self.CMD_HELP,
                                                formatter_class=SDKArgHelpFormatter)

        self.setup()

    def setup(self):
        """Sub classes should implement this method"""
        raise NotImplementedError()

    def execute_command(self, args):
        """Sub classes should implement this method"""
        raise NotImplementedError()

    @staticmethod
    def _get_common_parser():
        """
        Create a 'common parser' with all below arguments

        :return: A single argparse.ArgumentParser in a List
        :rtype: List
        """
        common_parser = argparse.ArgumentParser(add_help=False)

        common_parser.add_argument("-a", "--artifact_type",
                                   type=ensure_unicode,
                                   help="API names of artifact types to include",
                                   nargs="*")

        common_parser.add_argument("-d", "--datatable",
                                   type=ensure_unicode,
                                   help="API names of datatables to include",
                                   nargs="*")

        common_parser.add_argument("-e", "--export_file",
                                   type=ensure_unicode,
                                   help="Path to a local (.res) export file")

        common_parser.add_argument("-f", "--field",
                                   type=ensure_unicode,
                                   help="API names of custom fields to include",
                                   nargs="*")

        common_parser.add_argument("-fn", "--function",
                                   type=ensure_unicode,
                                   help="API names of functions to include",
                                   nargs="*")

        common_parser.add_argument("-m", "--msg_dest",
                                   type=ensure_unicode,
                                   help="API names of message destinations to include",
                                   nargs="*")

        common_parser.add_argument("-r", "--rule",
                                   type=ensure_unicode,
                                   help="Display names of rules to include (surrounded by '')",
                                   nargs="*")

        common_parser.add_argument("-s", "--script",
                                   type=ensure_unicode,
                                   help="Display names of scripts to include (surrounded by '')",
                                   nargs="*")

        common_parser.add_argument("-t", "--task",
                                   type=ensure_unicode,
                                   help="API names of custom tasks to include",
                                   nargs="*")

        common_parser.add_argument("-w", "--workflow",
                                   type=ensure_unicode,
                                   help="API names of workflows to include",
                                   nargs="*")

        return [common_parser]
