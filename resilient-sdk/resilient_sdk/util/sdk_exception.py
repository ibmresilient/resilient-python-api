#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

""" Python Module that exposes the SDKException class """


class SDKException(Exception):
    """Custom Exception for resilient-sdk"""

    # Class variable to track what resilient-sdk command was run
    # This should be set at the start of the execute_command() method of each sub class of the BaseCmd class
    command_ran = ""

    def __init__(self, message):
        if not SDKException.command_ran:
            SDKException.command_ran = "<no subcommand provided>"

        self.message = "\n'resilient-sdk %s' FAILED\nERROR: %s" % (SDKException.command_ran, message)

        # Call the base class
        super(SDKException, self).__init__(message)

    def __str__(self):
        return self.message
