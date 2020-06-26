#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

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

    # Set this in sub-class. Its a list of strings of parser names that will be included:
    # - "res_obj_parser"
    # - "io_parser"
    # - "zip_parser"
    CMD_ADD_PARSERS = []

    def __init__(self, sub_parser):

        assert self.CMD_NAME
        assert self.CMD_HELP

        parser_parents = []

        if "res_obj_parser" in self.CMD_ADD_PARSERS:
            parser_parents.append(self._get_res_obj_parser())

        if "io_parser" in self.CMD_ADD_PARSERS:
            parser_parents.append(self._get_io_parser())

        if "zip_parser" in self.CMD_ADD_PARSERS:
            parser_parents.append(self._get_zip_parser())

        self.parser = sub_parser.add_parser(self.CMD_NAME,
                                            help=self.CMD_HELP,
                                            formatter_class=SDKArgHelpFormatter,
                                            parents=parser_parents)

        # Rename "optionals" to "options"
        self.parser._optionals.title = "options"

        self.setup()

    def setup(self):
        """Sub classes should implement this method"""
        raise NotImplementedError()

    def execute_command(self, args):
        """Sub classes should implement this method"""
        raise NotImplementedError()

    @staticmethod
    def _get_res_obj_parser():
        """
        Create a parser that contains arguments for all Resilient Object Types

        :return: A single argparse.ArgumentParser
        :rtype: argparse.ArgumentParser
        """
        res_obj_parser = argparse.ArgumentParser(add_help=False)

        res_obj_parser.add_argument("-a", "--artifacttype",
                                    type=ensure_unicode,
                                    help="API names of artifact types to include",
                                    nargs="*")

        res_obj_parser.add_argument("-d", "--datatable",
                                    type=ensure_unicode,
                                    help="API names of datatables to include",
                                    nargs="*")

        res_obj_parser.add_argument("-fd", "--field",
                                    type=ensure_unicode,
                                    help="API names of custom fields to include",
                                    nargs="*")

        res_obj_parser.add_argument("-f", "--function",
                                    type=ensure_unicode,
                                    help="API names of functions to include",
                                    nargs="*")

        res_obj_parser.add_argument("-m", "--messagedestination",
                                    type=ensure_unicode,
                                    help="API names of message destinations to include",
                                    nargs="*")

        res_obj_parser.add_argument("-r", "--rule",
                                    type=ensure_unicode,
                                    help="Display names of rules to include (surrounded by \"\")",
                                    nargs="*")

        res_obj_parser.add_argument("-s", "--script",
                                    type=ensure_unicode,
                                    help="Display names of scripts to include (surrounded by \"\")",
                                    nargs="*")

        res_obj_parser.add_argument("-t", "--task",
                                    type=ensure_unicode,
                                    help="API names of custom tasks to include",
                                    nargs="*")

        res_obj_parser.add_argument("-w", "--workflow",
                                    type=ensure_unicode,
                                    help="API names of workflows to include",
                                    nargs="*")

        return res_obj_parser

    @staticmethod
    def _get_io_parser():
        """
        Create a parser that contains arguments for handling file output

        :return: A single argparse.ArgumentParser
        :rtype: argparse.ArgumentParser
        """
        io_parser = argparse.ArgumentParser(add_help=False)

        io_parser.add_argument("-e", "--exportfile",
                               type=ensure_unicode,
                               help="Path to a local (.res or .resz) export file")

        io_parser.add_argument("-o", "--output",
                               type=ensure_unicode,
                               help="Path to output directory. Uses current dir by default")

        return io_parser

    @staticmethod
    def _get_zip_parser():
        """
        Create a parser that contains arguments for handling zip files

        :return: A single argparse.ArgumentParser
        :rtype: argparse.ArgumentParser
        """
        zip_parser = argparse.ArgumentParser(add_help=False)

        zip_parser.add_argument("-z", "--zip",
                                action="store_true",
                                help="Generate a .zip of the generated file")

        return zip_parser
