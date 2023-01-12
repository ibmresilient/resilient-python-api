#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import os
import sys

import pytest
from mock import patch
from resilient_sdk.cmds import CmdValidate, base_cmd
from resilient_sdk.util import constants, sdk_validate_configs
from resilient_sdk.util.sdk_validate_issue import SDKValidateIssue
from tests.shared_mock_data import mock_paths


def test_cmd_validate_setup(fx_copy_fn_main_mock_integration, fx_get_sub_parser, fx_cmd_line_args_validate):
    cmd_validate = CmdValidate(fx_get_sub_parser)

    assert isinstance(cmd_validate, base_cmd.BaseCmd)
    assert cmd_validate.CMD_NAME == "validate"
    assert cmd_validate.CMD_HELP == "Tests the content of all files associated with the app, including code, before packaging it. Only Python >= 3.6 supported."
    assert cmd_validate.CMD_USAGE == """
    $ resilient-sdk validate -p <name_of_package>
    $ resilient-sdk validate -p <name_of_package> -c '/usr/custom_app.config'
    $ resilient-sdk validate -p <name_of_package> --validate
    $ resilient-sdk validate -p <name_of_package> --tests
    $ resilient-sdk validate -p <name_of_package> --tests --tox-args resilient_password="secret_pwd" resilient_host="ibmsoar.example.com"
    $ resilient-sdk validate -p <name_of_package> --tests --settings <path_to_custom_sdk_settings_file>
    $ resilient-sdk validate -p <name_of_package> --pylint --bandit --selftest"""
    assert cmd_validate.CMD_DESCRIPTION == cmd_validate.CMD_HELP

    args = cmd_validate.parser.parse_known_args()[0]
    assert args.package == "fn_main_mock_integration"
    assert bool(not args.validate and not args.tests and not args.pylint and not args.bandit) is True


def test_print_package_details(fx_copy_fn_main_mock_integration, fx_get_sub_parser, fx_cmd_line_args_validate, caplog):

    cmd_validate = CmdValidate(fx_get_sub_parser)
    args = cmd_validate.parser.parse_known_args()[0]
    assert args.package == "fn_main_mock_integration"
    # set package name to path to package
    args.package = fx_copy_fn_main_mock_integration[1]
    cmd_validate._print_package_details(args)

    assert "Printing details" in caplog.text
    assert "name: fn_main_mock_integration" in caplog.text
    assert "Proxies not fully supported" in caplog.text


def test_print_package_details_proxy_supported(fx_copy_fn_main_mock_integration, fx_get_sub_parser, fx_cmd_line_args_validate, caplog):

    cmd_validate = CmdValidate(fx_get_sub_parser)
    args = cmd_validate.parser.parse_known_args()[0]
    assert args.package == "fn_main_mock_integration"

    # set package name to path to package
    args.package = fx_copy_fn_main_mock_integration[1]

    with patch("resilient_sdk.cmds.validate.package_helpers.get_dependency_from_install_requires") as mock_dep:

        mock_dep.return_value = "resilient_circuits>={0}".format(constants.RESILIENT_VERSION_WITH_PROXY_SUPPORT)
        cmd_validate._print_package_details(args)

        assert "Printing details" in caplog.text
        assert "name: fn_main_mock_integration" in caplog.text
        assert "Proxies supported" in caplog.text


def test_pass_validate_setup_py_file(fx_copy_fn_main_mock_integration):
    """Test for success when calling _validate_setup()"""

    mock_package_path = fx_copy_fn_main_mock_integration[1]

    mock_data = [
        ("test", {
            "fail_func": lambda x: False,
            "parse_func": lambda _, attr_list: {attr: "mock_data" for attr in attr_list},
        })
    ]

    with patch.object(sdk_validate_configs, "setup_py_attributes", mock_data):
        results = CmdValidate._validate_setup(mock_package_path)

        assert results[0]
        assert len(results) == 2
        assert len(results[1]) == 1
        assert results[1][0].severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG


def test_fail_validate_setup_py_file(fx_copy_fn_main_mock_integration):
    """Test for failure when calling _validate_setup()"""

    mock_package_path = fx_copy_fn_main_mock_integration[1]
        
    mock_data = [
        ("test2", {
            "fail_func": lambda x: True,
            "fail_msg": "failed",
            "severity": SDKValidateIssue.SEVERITY_LEVEL_WARN,
            "missing_msg": "missing",
            "solution": "solution",
            "parse_func": lambda _, attr_list: {attr: "mock_data" for attr in attr_list},
        }),
        ("test", {
            "fail_func": lambda x: True,
            "fail_msg": "failed",
            "severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
            "missing_msg": "missing",
            "solution": "solution",
            "parse_func": lambda _, attr_list: {attr: "mock_data" for attr in attr_list},
        }),
        ("test3", {
            "fail_func": lambda x: True,
            "fail_msg": "failed",
            "severity": SDKValidateIssue.SEVERITY_LEVEL_INFO,
            "missing_msg": "missing",
            "solution": "solution",
            "parse_func": lambda _, attr_list: {attr: "mock_data" for attr in attr_list},
        }),
        ("test4", {
            "fail_func": lambda x: True,
            "fail_msg": "failed",
            "severity": SDKValidateIssue.SEVERITY_LEVEL_INFO,
            "solution": "solution",
            "parse_func": lambda _, attr_list: {"attr": False},
        })
    ]

    with patch.object(sdk_validate_configs, "setup_py_attributes", mock_data):
        results = CmdValidate._validate_setup(mock_package_path)

        assert not results[0]
        assert len(results) == 2
        assert len(results[1]) == 3
        # note the returned values in results[1] are sorted so the levels should be in order of severity
        assert results[1][0].severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
        assert results[1][1].severity == SDKValidateIssue.SEVERITY_LEVEL_WARN
        assert results[1][2].severity == SDKValidateIssue.SEVERITY_LEVEL_INFO

def test_pass_validate_selftest_py_file(fx_get_sub_parser, fx_cmd_line_args_validate, fx_copy_fn_main_mock_integration):

    cmd_validate = CmdValidate(fx_get_sub_parser)
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


def test_fail_validate_selftest_py_file(fx_get_sub_parser, fx_cmd_line_args_validate, fx_copy_fn_main_mock_integration):

    cmd_validate = CmdValidate(fx_get_sub_parser)
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

def test_pass_validate_package_files(fx_copy_fn_main_mock_integration):

    mock_path_package = fx_copy_fn_main_mock_integration[1]
    mock_data = [ 
        ("mock_valid_file", {"func": lambda **_: [SDKValidateIssue("pass", "pass", SDKValidateIssue.SEVERITY_LEVEL_DEBUG)]})
     ]

    # the file isn't actually real so we need to mock the validate_file_paths call to not raise and error
    with patch("resilient_sdk.cmds.validate.sdk_helpers.validate_file_paths") as mock_validate_file:
        mock_validate_file.return_value = None

        # mock the package_file data to mock_data
        with patch("resilient_sdk.cmds.validate.validation_configurations.package_files", new=mock_data):

            results = CmdValidate._validate_package_files(mock_path_package)

            assert len(results) == 2
            assert results[0]
            assert len(results[1]) == 1
            assert results[1][0].severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_fail_validate_package_files(fx_copy_fn_main_mock_integration):

    mock_path_package = fx_copy_fn_main_mock_integration[1]
    mock_data = [ 
        ("mock_valid_file", {"func": lambda **_: [SDKValidateIssue("pass", "pass", SDKValidateIssue.SEVERITY_LEVEL_DEBUG)]}),
        ("mock_invalid_file", {"func": lambda **_: [SDKValidateIssue("fail", "fail")]})
     ]

    # the file isn't actually real so we need to mock the validate_file_paths call to not raise and error
    with patch("resilient_sdk.cmds.validate.sdk_helpers.validate_file_paths") as mock_validate_file:
        mock_validate_file.return_value = None

        # mock the package_file data to mock_data
        with patch("resilient_sdk.cmds.validate.validation_configurations.package_files", new=mock_data):

            results = CmdValidate._validate_package_files(mock_path_package)

            assert len(results) == 2
            assert not results[0]
            assert len(results[1]) == 2

            # note that the results should be sorted so the critical issue comes up first
            assert results[1][0].severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
            assert results[1][1].severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_file_not_found_validate_package_files(fx_copy_fn_main_mock_integration):
    mock_path_package = fx_copy_fn_main_mock_integration[1]
    mock_data = [ 
        ("mock_missing_file", {
            "missing_name": "mock_name",
            "missing_msg": "mock_msg {0}",
            "missing_severity": SDKValidateIssue.SEVERITY_LEVEL_CRITICAL,
            "missing_solution": "mock_solution"
        })
     ]

    # mock the package_file data to mock_data
    with patch("resilient_sdk.cmds.validate.validation_configurations.package_files", new=mock_data):

        results = CmdValidate._validate_package_files(mock_path_package)

        assert len(results) == 2
        assert not results[0]
        assert len(results[1]) == 1
        assert mock_path_package in results[1][0].description
        assert results[1][0].severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
        assert results[1][0].solution == "mock_solution"

def test_payloads_validate_package_files(fx_copy_fn_main_mock_integration):
    # this uses the payload samples in the mock integration

    mock_path_package = fx_copy_fn_main_mock_integration[1]

    results = CmdValidate._validate_payload_samples(mock_path_package)

    assert len(results) == 2
    assert not results[0]
    assert len(results[1]) == 4
    assert "'output_json_example.json' and 'output_json_schema.json' for 'a_mock_function_with_no_unicode_characters_in_name' empty" in results[1][0].description
    assert "'output_json_example.json' and 'output_json_schema.json' for 'mock_function__three' empty" in results[1][1].description
    assert "'output_json_schema.json' for 'mock_function_one' empty" in results[1][2].description
    assert "'output_json_example.json' and 'output_json_schema.json' for 'mock_function_two' empty" in results[1][3].description
    assert results[1][0].severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL


def test_pass_validate_tox_tests(fx_copy_fn_main_mock_integration):

    mock_path_package = fx_copy_fn_main_mock_integration[1]
    mock_data = [
        {"func": lambda **_: (1, SDKValidateIssue("pass", "pass", SDKValidateIssue.SEVERITY_LEVEL_DEBUG))}
    ]

    # mock the package_file data to mock_data
    with patch("resilient_sdk.cmds.validate.validation_configurations.tests_attributes", new=mock_data):

        results = CmdValidate._validate_tox_tests(mock_path_package)

        assert len(results) == 2
        assert results[0]
        assert len(results[1]) == 1
        assert results[1][0].severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_info_validate_tox_tests(fx_copy_fn_main_mock_integration):

    mock_path_package = fx_copy_fn_main_mock_integration[1]
    mock_data = [
        {"func": lambda **_: (-1, SDKValidateIssue("skip", "info: skip", SDKValidateIssue.SEVERITY_LEVEL_INFO))}
    ]

    # mock the package_file data to mock_data
    with patch("resilient_sdk.cmds.validate.validation_configurations.tests_attributes", new=mock_data):

        results = CmdValidate._validate_tox_tests(mock_path_package)

        assert len(results) == 2
        assert results[0] == -1
        assert len(results[1]) == 1
        assert results[1][0].severity == SDKValidateIssue.SEVERITY_LEVEL_INFO

def test_fail_validate_tox_tests(fx_copy_fn_main_mock_integration):

    mock_path_package = fx_copy_fn_main_mock_integration[1]
    mock_data = [
        {"func": lambda **_: (0, SDKValidateIssue("fail", "fail", SDKValidateIssue.SEVERITY_LEVEL_CRITICAL))}
    ]

    # mock the package_file data to mock_data
    with patch("resilient_sdk.cmds.validate.validation_configurations.tests_attributes", new=mock_data):

        results = CmdValidate._validate_tox_tests(mock_path_package)

        assert len(results) == 2
        assert results[0] == 0
        assert len(results[1]) == 1
        assert results[1][0].severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL


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
    cmd_validate.SUMMARY_LIST = mock_data
    cmd_validate._print_summary()

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


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="requires python3.6 or higher")
def test_custom_app_config_file(fx_copy_and_pip_install_fn_main_mock_integration, fx_cmd_line_args_validate, fx_get_sub_parser, fx_mock_res_client, caplog):
    mock_app_config_path = mock_paths.TEST_TEMP_DIR + "/mock_app.config"
    mock_integration_name = fx_copy_and_pip_install_fn_main_mock_integration[0]

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = fx_copy_and_pip_install_fn_main_mock_integration[1]

    # Add cmd line arg
    sys.argv.extend(["--selftest"])
    sys.argv.extend(["-c", mock_app_config_path])

    with patch("resilient_sdk.cmds.validate.sdk_helpers.get_resilient_client") as mock_client:

        mock_client.return_value = fx_mock_res_client
        cmd_validate = CmdValidate(fx_get_sub_parser)
        args = cmd_validate.parser.parse_known_args()[0]

        cmd_validate.execute_command(args)
        assert "Couldn't read config file '{0}'".format(mock_app_config_path) in caplog.text
        assert not os.getenv(constants.ENV_VAR_APP_CONFIG_FILE, default=None)


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="requires python3.6 or higher")
def test_not_using_custom_app_config_file(fx_copy_fn_main_mock_integration, fx_cmd_line_args_validate, fx_get_sub_parser, fx_mock_res_client):
    mock_integration_name = fx_copy_fn_main_mock_integration[0]

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = fx_copy_fn_main_mock_integration[1]

    # Add cmd line arg
    sys.argv.extend(["--selftest"])

    with patch("resilient_sdk.cmds.validate.sdk_helpers.get_resilient_client") as mock_client:

        mock_client.return_value = fx_mock_res_client
        cmd_validate = CmdValidate(fx_get_sub_parser)
        args = cmd_validate.parser.parse_known_args()[0]

        cmd_validate.execute_command(args)

        assert not os.getenv(constants.ENV_VAR_APP_CONFIG_FILE, default=None)


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="requires python3.6 or higher")
def test_run_tests_with_tox_args(fx_pip_install_tox, fx_copy_fn_main_mock_integration, fx_cmd_line_args_validate, fx_get_sub_parser, caplog):
    mock_integration_name = fx_copy_fn_main_mock_integration[0]

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = fx_copy_fn_main_mock_integration[1]

    # Add cmd line arg
    sys.argv.extend(["--tests", "--tox-args", 'arg1="val1"', 'arg2="val2"'])

    # remove the last call which is the one that actually runs the tox tests
    # this method is checked in other tests and is too slow to run here live
    with patch.object(sdk_validate_configs, "tests_attributes", sdk_validate_configs.tests_attributes[0:-1]):

        cmd_validate = CmdValidate(fx_get_sub_parser)
        args = cmd_validate.parser.parse_known_args()[0]

        cmd_validate.execute_command(args)

        assert "tests PASS" in caplog.text


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="requires python3.6 or higher")
def test_run_tests_with_settings_file(fx_pip_install_tox, fx_copy_fn_main_mock_integration, fx_cmd_line_args_validate, fx_mock_res_client, fx_get_sub_parser, caplog):
    mock_integration_name = fx_copy_fn_main_mock_integration[0]

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = fx_copy_fn_main_mock_integration[1]

    # Add cmd line arg
    sys.argv.extend(["--tests", "--settings", mock_paths.MOCK_SDK_SETTINGS_PATH])

    with patch.object(sdk_validate_configs, "tests_attributes", sdk_validate_configs.tests_attributes[0:-1]):
        with patch("resilient_sdk.cmds.validate.sdk_helpers.get_resilient_client") as mock_client:

            mock_client.return_value = fx_mock_res_client

            cmd_validate = CmdValidate(fx_get_sub_parser)
            args = cmd_validate.parser.parse_known_args()[0]

            cmd_validate.execute_command(args)

            assert "tests PASS" in caplog.text


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="requires python3.6 or higher")
def test_run_pylint_scan(fx_pip_install_pylint, fx_copy_fn_main_mock_integration, fx_cmd_line_args_validate, fx_get_sub_parser, caplog):

    # This test runs pylint on the fn_main_mock_integration
    # Because tests automatically run in DEBUG mode, all levels (R,C,W,E,F)
    # will be enabled for pylint. The integration should fail the scan with
    # a 6.27/10 score

    mock_integration_name = fx_copy_fn_main_mock_integration[0]

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = fx_copy_fn_main_mock_integration[1]

    # Add cmd line arg
    sys.argv.extend(["--pylint"])

    cmd_validate = CmdValidate(fx_get_sub_parser)
    args = cmd_validate.parser.parse_known_args()[0]

    cmd_validate.execute_command(args)

    assert "Running pylint" in caplog.text
    assert "--enable=R,C,W,E,F" in caplog.text
    assert "WARNING     The Pylint score was" in caplog.text


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="requires python3.6 or higher")
def test_run_bandit_scan(fx_pip_install_bandit, fx_copy_fn_main_mock_integration, fx_cmd_line_args_validate, fx_get_sub_parser, caplog):

    # This test runs bandit on the fn_main_mock_integration
    # The intergration should pass the bandit scan with no issues

    mock_integration_name = fx_copy_fn_main_mock_integration[0]

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = fx_copy_fn_main_mock_integration[1]

    # Add cmd line arg
    sys.argv.extend(["--bandit"])

    cmd_validate = CmdValidate(fx_get_sub_parser)
    args = cmd_validate.parser.parse_known_args()[0]

    cmd_validate.execute_command(args)

    assert "Running Bandit Scan" in caplog.text
    assert "Bandit scan passed" in caplog.text


def test_generate_report(fx_copy_fn_main_mock_integration, fx_cmd_line_args_validate, fx_get_sub_parser, caplog):
    mock_issues_dict = {
        "details": [
            ("a", "b")
        ]
    }
    mock_counts = {
        SDKValidateIssue.SEVERITY_LEVEL_CRITICAL: 0, 
        SDKValidateIssue.SEVERITY_LEVEL_WARN: 0, 
        SDKValidateIssue.SEVERITY_LEVEL_INFO: 0, 
        SDKValidateIssue.SEVERITY_LEVEL_DEBUG: 0
    }

    mock_integration_name = fx_copy_fn_main_mock_integration[0]
    path_package = fx_copy_fn_main_mock_integration[1]

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = path_package

    cmd_validate = CmdValidate(fx_get_sub_parser)
    args = cmd_validate.parser.parse_known_args()[0]

    cmd_validate._generate_report(mock_issues_dict, args, mock_counts)

    assert "Creating dist directory at" in caplog.text
    assert "Writing report to" in caplog.text

    assert os.path.exists(os.path.join(path_package, "dist/validate_report.md"))


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="requires python3.6 or higher")
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
        assert "setup.py attribute 'author' remains unchanged from the default value" in caplog.text
