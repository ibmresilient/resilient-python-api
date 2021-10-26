#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import os
import shutil
import sys

from mock import patch
from resilient_sdk.cmds import CmdValidate, base_cmd
from resilient_sdk.util.sdk_validate_issue import SDKValidateIssue
from tests.shared_mock_data import mock_paths


def test_cmd_validate_setup(fx_copy_fn_main_mock_integration, fx_get_sub_parser, fx_cmd_line_args_validate):
    cmd_validate = CmdValidate(fx_get_sub_parser)

    assert isinstance(cmd_validate, base_cmd.BaseCmd)
    assert cmd_validate.CMD_NAME == "validate"
    assert cmd_validate.CMD_HELP == "Validate an App before packaging it"
    assert cmd_validate.CMD_USAGE == """
    $ resilient-sdk validate -p <name_of_package>
    $ resilient-sdk validate -p <name_of_package> --validate
    $ resilient-sdk validate -p <name_of_package> --tests
    $ resilient-sdk validate -p <name_of_package> --pylint --bandit --cve --selftest"""
    assert cmd_validate.CMD_DESCRIPTION == cmd_validate.CMD_HELP

    args = cmd_validate.parser.parse_known_args()[0]
    assert args.package == "fn_main_mock_integration"
    assert bool(not args.validate and not args.tests and not args.pylint and not args.bandit and not args.cve) is True

def test_print_package_details(fx_copy_fn_main_mock_integration, fx_get_sub_parser, fx_cmd_line_args_validate, caplog):

    cmd_validate = CmdValidate(fx_get_sub_parser)
    args = cmd_validate.parser.parse_known_args()[0]
    assert args.package == "fn_main_mock_integration"
    # set package name to path to package
    args.package = fx_copy_fn_main_mock_integration[1]
    cmd_validate._print_package_details(args)

    assert "Printing details" in caplog.text
    assert "name: fn_main_mock_integration" in caplog.text
    assert "Proxy support: " in caplog.text

def test_pass_validate_setup_py_file(fx_copy_fn_main_mock_integration):
    """Test for success when calling _validate_setup()"""

    mock_package_path = fx_copy_fn_main_mock_integration[1]
        
    mock_data = {
        "test": {
            "fail_func": lambda x: False,
            "parse_func": lambda _, attr_list: {attr: "mock_data" for attr in attr_list},
        }
    }

    with patch.dict("resilient_sdk.cmds.validate.validation_configurations.setup_py_attributes", mock_data, clear=True):
        results = CmdValidate._validate_setup(mock_package_path)

        assert results[0]
        assert len(results) == 2
        assert len(results[1]) == 1
        assert results[1][0].severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_fail_validate_setup_py_file(fx_copy_fn_main_mock_integration):
    """Test for failure when calling _validate_setup()"""

    mock_package_path = fx_copy_fn_main_mock_integration[1]
        
    mock_data = {
        "test2": {
            "fail_func": lambda x: True,
            "fail_msg": "failed",
            "severity": SDKValidateIssue.SEVERITY_LEVEL_WARN,
            "missing_msg": "missing",
            "solution": "solution",
            "parse_func": lambda _, attr_list: {attr: "mock_data" for attr in attr_list},
        },
        "test": {
            "fail_func": lambda x: True,
            "fail_msg": "failed",
            "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
            "missing_msg": "missing",
            "solution": "solution",
            "parse_func": lambda _, attr_list: {attr: "mock_data" for attr in attr_list},
        },
        "test3": {
            "fail_func": lambda x: True,
            "fail_msg": "failed",
            "severity": SDKValidateIssue.SEVERITY_LEVEL_INFO,
            "missing_msg": "missing",
            "solution": "solution",
            "parse_func": lambda _, attr_list: {attr: "mock_data" for attr in attr_list},
        }
    }

    with patch.dict("resilient_sdk.cmds.validate.validation_configurations.setup_py_attributes", mock_data, clear=True):
        results = CmdValidate._validate_setup(mock_package_path)

        assert not results[0]
        assert len(results) == 2
        assert len(results[1]) == 3
        # note the returned values in results[1] are sorted so the levels should be in order of severity
        assert results[1][0].severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
        assert results[1][1].severity == SDKValidateIssue.SEVERITY_LEVEL_WARN
        assert results[1][2].severity == SDKValidateIssue.SEVERITY_LEVEL_INFO

def test_pass_validate_selftest_py_file(fx_copy_fn_main_mock_integration):

    mock_package_path = fx_copy_fn_main_mock_integration[1]
    mock_data = [
        { "func": lambda **x: (True, SDKValidateIssue("pass", "pass", SDKValidateIssue.SEVERITY_LEVEL_DEBUG)) }
    ]

    with patch("resilient_sdk.cmds.validate.validation_configurations.selftest_attributes", new=mock_data):
        results = CmdValidate._validate_selftest(mock_package_path)

        assert results[0]
        assert len(results) == 2
        assert len(results[1]) == 1
        assert results[1][0].severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG


def test_fail_validate_selftest_py_file(fx_copy_fn_main_mock_integration):

    mock_package_path = fx_copy_fn_main_mock_integration[1]
    mock_data = [
        { "func": lambda **x: (True, SDKValidateIssue("pass", "pass", SDKValidateIssue.SEVERITY_LEVEL_DEBUG)) },
        { "func": lambda **x: (False, SDKValidateIssue("fail", "fail")) }
    ]

    with patch("resilient_sdk.cmds.validate.validation_configurations.selftest_attributes", new=mock_data):
        results = CmdValidate._validate_selftest(mock_package_path)

        assert not results[0]
        assert len(results) == 2
        assert len(results[1]) == 2
        assert results[1][0].severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
        assert results[1][1].severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_get_log_level():
    assert CmdValidate._get_log_level(int("50")) == 10 # should only work on str's (returns DEBUG when given an int)

    assert CmdValidate._get_log_level("DEBUG") == 10
    assert CmdValidate._get_log_level("INFO") == 20
    assert CmdValidate._get_log_level("WARNING") == 30
    assert CmdValidate._get_log_level("CRITICAL") == 40

    assert CmdValidate._get_log_level("CRITICAL", True) == 10 # when outputsuppressed == True, returns 10

    assert CmdValidate._get_log_level("SOMESTRING") == 10


def test_print_summary(fx_get_sub_parser, caplog):
    mock_data = [
        SDKValidateIssue("default", "severity is used"),
        SDKValidateIssue("default", "severity is used"),
        SDKValidateIssue("default", "severity is used"),
        SDKValidateIssue("warning", "severity", SDKValidateIssue.SEVERITY_LEVEL_WARN),
        SDKValidateIssue("warning", "severity", SDKValidateIssue.SEVERITY_LEVEL_WARN),
        SDKValidateIssue("debug", "pass", SDKValidateIssue.SEVERITY_LEVEL_DEBUG)
    ]
    cmd_validate = CmdValidate(fx_get_sub_parser)
    cmd_validate._print_summary(mock_data)

    assert "Validation Results" in caplog.text
    assert "Critical Issues:     3" in caplog.text
    assert "Warnings:            2" in caplog.text
    assert "Validations Passed:  1" in caplog.text

def test_print_status(fx_get_sub_parser, caplog):
    cmd_validate = CmdValidate(fx_get_sub_parser)
    cmd_validate._print_status("INFO", "testprintstatus", True)
    assert "testprintstatus PASS" in caplog.text

    cmd_validate._print_status("INFO", "testprintstatus", False)
    assert "testprintstatus FAIL" in caplog.text

def test_execute_command(fx_copy_fn_main_mock_integration, fx_cmd_line_args_validate, fx_get_sub_parser, fx_mock_res_client, caplog):

    mock_integration_name = fx_copy_fn_main_mock_integration[0]

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = fx_copy_fn_main_mock_integration[1]

    # Add cmd line arg
    sys.argv.extend(["--validate"])

    with patch("resilient_sdk.cmds.validate.sdk_helpers.get_resilient_client") as mock_client:

        mock_client.return_value = fx_mock_res_client
        cmd_validate = CmdValidate(fx_get_sub_parser)
        args = cmd_validate.parser.parse_known_args()[0]

        cmd_validate.execute_command(args)
        assert "Printing details" in caplog.text
        assert "Validation Results" in caplog.text
        assert u"ล ฦ ว ศ ษ ส ห ฬ อ" in caplog.text
        assert "setup.py attribute 'author' appears to still be the default value" in caplog.text
