#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import os, pkg_resources
from mock import patch
from resilient_sdk.util import constants, sdk_validate_helpers, sdk_validate_configs
from resilient_sdk.util.sdk_validate_issue import SDKValidateIssue
from tests.shared_mock_data import mock_paths

def test_selftest_validate_resilient_circuits_installed():

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.get_package_version") as mock_package_version:
        mock_package_version.return_value = pkg_resources.parse_version(constants.RESILIENT_LIBRARIES_VERSION)
        
        result = sdk_validate_helpers.selftest_validate_resilient_circuits_installed(sdk_validate_configs.selftest_attributes[0])
        assert isinstance(result[0], bool)
        assert isinstance(result[1], SDKValidateIssue)

        assert len(result) == 2
        assert result[0]
        assert result[1].solution is ""
        assert "'{0}' found in env".format(constants.CIRCUITS_PACKAGE_NAME) in result[1].name


def test_valid_selftest_validate_package_installed():

    mock_package_name = "resilient-sdk"
    # path_to_package is only used for outputting a solution to install
    mock_path_to_package = "fake/path/to/package"

    # positive case
    attr_dict = sdk_validate_configs.selftest_attributes[1]
    result = sdk_validate_helpers.selftest_validate_package_installed(attr_dict, mock_package_name, mock_path_to_package)

    assert len(result) == 2
    assert result[0]
    assert result[1].solution is ""


def test_invalid_selftest_validate_package_installed():

    mock_package_name = "fake-package-not-found"
    # path_to_package is only used for outputting a solution to install
    mock_path_to_package = "fake/path/to/package"

    # negative case
    attr_dict = sdk_validate_configs.selftest_attributes[1]
    result = sdk_validate_helpers.selftest_validate_package_installed(attr_dict, mock_package_name, mock_path_to_package)

    assert len(result) == 2
    assert result[0] is False
    assert mock_path_to_package in result[1].solution
    assert "not found" in result[1].name

def test_valid_selftest_validate_selftestpy_file_exists(fx_copy_fn_main_mock_integration):

    attr_dict = sdk_validate_configs.selftest_attributes[2]

    path_selftest = os.path.join(mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_UTIL, "selftest.py")

    result = sdk_validate_helpers.selftest_validate_selftestpy_file_exists(attr_dict, path_selftest)

    assert len(result) == 2
    assert result[0]
    assert "selftest.py found" in result[1].name

def test_invalid_selftest_validate_selftestpy_file_exists():

    attr_dict = sdk_validate_configs.selftest_attributes[2]

    path_selftest = "pacakge/with/no/util/selftest.py"

    result = sdk_validate_helpers.selftest_validate_selftestpy_file_exists(attr_dict, path_selftest)

    assert len(result) == 2
    assert result[0] is False
    assert "selftest.py not found" in result[1].name
    
def test_sefltest_run_selftestpy_valid():

    attr_dict = sdk_validate_configs.selftest_attributes[3]

    package_name = "fake_package_name"

    class MockSubProcessResult:
        stderr = b"Success"
        returncode = 0

    with patch("resilient_sdk.util.sdk_validate_helpers.subprocess.run") as mock_subprocess:
        
        mock_subprocess.return_value = MockSubProcessResult()

        result = sdk_validate_helpers.selftest_run_selftestpy(attr_dict, package_name)

        assert len(result) == 2
        assert result[0]
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_sefltest_run_selftestpy_invalid(fx_copy_fn_main_mock_integration):

    attr_dict = sdk_validate_configs.selftest_attributes[3]

    package_name = "fake_package_name"

    class MockSubProcessResult:
        stderr = b"failure {'state': 'failure', 'reason': 'failed for test reasons'} and more text here..."
        returncode = 1

    with patch("resilient_sdk.util.sdk_validate_helpers.subprocess.run") as mock_subprocess:
        
        mock_subprocess.return_value = MockSubProcessResult()

        result = sdk_validate_helpers.selftest_run_selftestpy(attr_dict, package_name)

        assert len(result) == 2
        assert result[0] is False
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
        assert "failed for test reasons" in result[1].description and package_name in result[1].description

def test_sefltest_run_selftestpy_rest_error(fx_copy_fn_main_mock_integration):

    attr_dict = sdk_validate_configs.selftest_attributes[3]

    package_name = "fake_package_name"

    class MockSubProcessResult:
        stderr = b"ERROR: (fake) issue connecting to SOAR"
        returncode = 20

    with patch("resilient_sdk.util.sdk_validate_helpers.subprocess.run") as mock_subprocess:
        
        mock_subprocess.return_value = MockSubProcessResult()

        result = sdk_validate_helpers.selftest_run_selftestpy(attr_dict, package_name)

        assert len(result) == 2
        assert result[0] is False
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
        assert MockSubProcessResult().stderr.decode("utf-8") in result[1].description