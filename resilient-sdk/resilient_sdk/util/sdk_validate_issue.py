#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

"""SDKValidateIssue class that enables describes an issue"""

import logging
from resilient_sdk.util import sdk_helpers

# Get the same logger object that is used in app.py
LOG = logging.getLogger(sdk_helpers.LOGGER_NAME)

# TODO: write unit tests


class SDKValidateIssue(object):
    SEVERITY_LEVEL_HIGH = 1
    SEVERITY_LEVEL_MED = 2
    SEVERITY_LEVEL_LOW = 3

    def __init__(self, name, description, severity=SEVERITY_LEVEL_HIGH, solution="UNKNOWN"):

        self.name = name
        self.description = description
        self.severity = severity
        self.solution = solution

    def __eq__(self, other):
        return self.severity == other.severity

    def __lt__(self, other):
        return self.severity < other.severity

    def __le__(self, other):
        return self.severity <= other.severity

    def __str__(self):
        return "'name={0}; description={1}; severity={2}; solution={3}'".format(self.name, self.description, 
                                                                    self._get_severity_as_str(), self.solution)

    def __short_str__(self):
        return "'issue={0}, severtiy={1}'".format(self.name, self.severity)

    def __repr__(self):
        return self.__str__()

    def _get_severity_as_str(self):
        return "HIGH" if self.severity == SDKValidateIssue.SEVERITY_LEVEL_HIGH else \
                "MEDIUM" if self.severity == SDKValidateIssue.SEVERITY_LEVEL_MED else \
                "LOW" if self.severity == SDKValidateIssue.SEVERITY_LEVEL_LOW else "UNKNOWN"

    def _get_formatted_severity_error_level(self):
        return "ERROR:\t" if self.severity == SDKValidateIssue.SEVERITY_LEVEL_HIGH else \
                "WARNING:" if self.severity == SDKValidateIssue.SEVERITY_LEVEL_MED else "INFO:\t"

    def get_logging_level(self):
        """
        Returns logging level to use with logger
        
        40=LOG.error
        30=LOG.warning
        20=LOG.info

        https://docs.python.org/3.5/library/logging.html#levels
        """
        if self.severity == SDKValidateIssue.SEVERITY_LEVEL_HIGH:
            return 40
        elif self.severity == SDKValidateIssue.SEVERITY_LEVEL_MED:
            return 30
        else:
            return 20

    def as_dict(self):
        """Returns this class object as a dictionary"""
        return self.__dict__

    def error_str(self):
        """Returns an error string to be output to the console"""
        return "{0}\t{1}; \n\t\tseverity={2}; \n\t\tsolution: {3}\n".format(self._get_formatted_severity_error_level(), 
                                                                  self.description, self._get_severity_as_str(), self.solution)