#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

"""SDKValidateIssue class that enables describes an issue"""

import logging
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util import package_file_helpers as package_helpers

# Get the same logger object that is used in app.py
LOG = logging.getLogger(sdk_helpers.LOGGER_NAME)

# TODO: write unit tests


class SDKValidateIssue(object):
    SEVERITY_LEVEL_CRITICAL = 1
    SEVERITY_LEVEL_WARN = 2
    SEVERITY_LEVEL_INFO = 3
    SEVERITY_LEVEL_DEBUG = 100

    def __init__(self, name, description, severity=SEVERITY_LEVEL_CRITICAL, solution="UNKNOWN"):

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
        return "CRITICAL" if self.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL else \
               "WARNING" if self.severity == SDKValidateIssue.SEVERITY_LEVEL_WARN else \
               "INFO" if self.severity == SDKValidateIssue.SEVERITY_LEVEL_INFO else "PASS"

    def as_dict(self):
        """Returns this class object as a dictionary"""
        return self.__dict__

    def get_logging_level(self, output_suppressed):
        """
        Returns logging level to use with logger
        
        50=LOG.critical
        40=LOG.error
        30=LOG.warning
        20=LOG.info
        10=LOG.debug

        https://docs.python.org/3.5/library/logging.html#levels
        """
        if output_suppressed:
            return 10

        if self.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL:
            return 40
        elif self.severity == SDKValidateIssue.SEVERITY_LEVEL_WARN:
            return 30
        elif self.severity == SDKValidateIssue.SEVERITY_LEVEL_INFO:
            return 20
        else:
            return 10

    def error_str(self):
        """Returns an error string to be output to the console"""
        return "{0:<20} {1}. \n{3:<11} {2}".format(
            package_helpers.color_output(self._get_severity_as_str(), self._get_severity_as_str()), 
            self.description, self.solution, ""
        )