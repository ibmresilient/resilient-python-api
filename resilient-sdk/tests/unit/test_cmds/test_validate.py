#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import shutil, os, sys
from mock import patch
from resilient_sdk.cmds import base_cmd, CmdValidate
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

def test_pass_validate_setup_py_file(fx_copy_fn_main_mock_integration):

    mock_package_path = fx_copy_fn_main_mock_integration[1]
        
    mock_data = {
        "test": {
            "fail_func": lambda x: False,
            "fail_msg": "failed",
            "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
            "missing_msg": "missing",
            "solution": "solution",
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
        assert "setup.py attribute 'author' appears to still be the default value" in caplog.text
