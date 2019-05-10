#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

""" Python Module that exposes the ExtException class """


class ExtException(Exception):
    """Custom Exception for ext commands"""

    # Class variable to track what resilient-circuits ext: command was run
    # This is set in the __init__ of the Ext class
    command_ran = ""

    def __init__(self, message):
        self.message = "\nresilient-circuits %s FAILED\nERROR: %s" % (ExtException.command_ran, message)

        # Call the base class
        super(ExtException, self).__init__(message)

    def __str__(self):
        return self.message
