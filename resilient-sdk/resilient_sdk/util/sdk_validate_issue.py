#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

"""SDKValidateIssue class that enables describes an issue"""

import logging

from resilient_sdk.util import constants
from resilient_sdk.util import package_file_helpers as package_helpers

# Get the same logger object that is used in app.py
LOG = logging.getLogger(constants.LOGGER_NAME)


class SDKValidateIssue(object):
    SEVERITY_LEVEL_CRITICAL = 1
    SEVERITY_LEVEL_WARN = 2
    SEVERITY_LEVEL_INFO = 3
    SEVERITY_LEVEL_DEBUG = 100

    def __init__(self, name, description, severity=SEVERITY_LEVEL_CRITICAL, solution="SOLUTION UNKNOWN"):

        self.name = name
        self.description = description
        self.severity = severity
        self.solution = solution

    def __eq__(self, other):
        """Checks equality of two SDKValidateIssue objs"""
        return self.severity == other.severity

    def __lt__(self, other):
        """Checks less than for two SDKValidateIssue objs"""
        return self.severity < other.severity

    def __le__(self, other):
        """Checks less than or equal to for two SDKValidateIssue objs"""
        return self.severity <= other.severity

    def __str__(self):
        """Returns string representation of a SDKValidateIssue obj"""
        return u"'name={0}; description={1}; severity={2}; solution={3}'".format(self.name, self.description, 
                                                                    self.get_logging_level(), self.solution)

    def __short_str__(self):
        """Short string representation of a SDKValidateIssue obj"""
        return u"'issue={0}, severtiy={1}'".format(self.name, self.severity)

    def __repr__(self):
        return self.__str__()

    def as_dict(self):
        """Returns this class object as a dictionary"""
        return self.__dict__

    def get_logging_level(self):
        """
        Returns logging level to use with CmdValidate._get_log_level
        
        :return: string indicating the error level that maps severity with constants.VALIDATE_LOG_LEVEL_[level]
        :rtype: str
        """

        if self.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL:
            return constants.VALIDATE_LOG_LEVEL_CRITICAL
        elif self.severity == SDKValidateIssue.SEVERITY_LEVEL_WARN:
            return constants.VALIDATE_LOG_LEVEL_WARNING
        elif self.severity == SDKValidateIssue.SEVERITY_LEVEL_INFO:
            return constants.VALIDATE_LOG_LEVEL_INFO
        else:
            return constants.VALIDATE_LOG_LEVEL_DEBUG

    def error_str(self):
        """Returns an error string to be output to the console"""
        return u"{0:<20} {1}\n{3:<11} {2}".format(
            package_helpers.color_output(
                self.get_logging_level() if self.get_logging_level() != constants.VALIDATE_LOG_LEVEL_DEBUG
                    else "PASS", 
                self.get_logging_level()), 
            self.description, self.solution, ""
        )

    def severity_to_color(self):
        """Returns a string representing HTML value of the severity. For Jinja2 templating"""

        color = "red" if self.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL else "orange" if self.severity == SDKValidateIssue.SEVERITY_LEVEL_WARN else "teal"

        return '<span style="color:{0}">{1}</span>'.format(color, self.get_logging_level())
