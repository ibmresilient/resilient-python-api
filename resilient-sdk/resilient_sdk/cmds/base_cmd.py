#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.


class BaseCmd(object):
    """TODO Docstring"""

    CMD_NAME = None
    CMD_HELP = None
    CMD_USAGE = None
    CMD_DESCRIPTION = None

    def __init__(self, cmd_name, cmd_help, sub_parser):
        self.parser = sub_parser.add_parser(cmd_name, help=cmd_help)
        self.setup()

    def setup(self):
        """Sub classes should implement this method"""
        raise NotImplementedError()

    def execute_command(self, args):
        """Sub classes should implement this method"""
        raise NotImplementedError()
