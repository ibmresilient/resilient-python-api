#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import pytest
from resilient_sdk.util import constants
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util.sdk_validate_issue import SDKValidateIssue


def mock_warning_issue():
    return SDKValidateIssue(
        "this issue failed",
        "description of failed issue",
        SDKValidateIssue.SEVERITY_LEVEL_WARN,
        "here's a solution"
    )

def mock_issue_with_defaults():
    return SDKValidateIssue("name is name", "a simple description")

def mock_debug_issue():
    return SDKValidateIssue("bugged", "descr", SDKValidateIssue.SEVERITY_LEVEL_DEBUG, "can't fix")

    

def test_sdk_validate_issue_warning():

    issue = mock_warning_issue()

    assert issue.get_logging_level() == constants.VALIDATE_LOG_LEVEL_WARNING
    assert issue < mock_debug_issue()
    assert issue > mock_issue_with_defaults()
    assert package_helpers.COLORS["WARNING"] in issue.error_str()

def test_sdk_validate_issue_with_defaults():

    issue = mock_issue_with_defaults()
    
    assert issue.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    assert issue.get_logging_level() == constants.VALIDATE_LOG_LEVEL_CRITICAL
    assert package_helpers.COLORS["CRITICAL"] in issue.error_str()

def test_sdk_validate_issue_debug():
    
    issue = mock_debug_issue()

    assert issue.severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG
    assert issue.get_logging_level() == constants.VALIDATE_LOG_LEVEL_DEBUG
    assert package_helpers.COLORS["PASS"] in issue.error_str()
