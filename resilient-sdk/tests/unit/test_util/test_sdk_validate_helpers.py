#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2024. All Rights Reserved.

import difflib
import os
import sys

import pytest
import tests.shared_mock_data.sdk_mock_paths as mock_paths
from mock import patch
from packaging.version import parse
from resilient_sdk.util import (constants, sdk_validate_configs,
                                sdk_validate_helpers)
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util.sdk_validate_issue import SDKValidateIssue


def test_selftest_validate_resilient_circuits_installed():

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.get_package_version") as mock_package_version:
        mock_package_version.return_value = parse(constants.RESILIENT_LIBRARIES_VERSION)

        result = sdk_validate_helpers.selftest_validate_resilient_circuits_installed(sdk_validate_configs.selftest_attributes[0])
        assert isinstance(result[0], bool)
        assert isinstance(result[1], SDKValidateIssue)

        assert len(result) == 2
        assert result[0]
        assert result[1].solution == ""
        assert "selftest" in result[1].name


def test_valid_selftest_validate_package_installed():

    mock_package_name = "resilient-sdk"
    # path_to_package is only used for outputting a solution to install
    mock_path_to_package = "fake/path/to/package"

    # positive case
    attr_dict = sdk_validate_configs.selftest_attributes[1]
    result = sdk_validate_helpers.selftest_validate_package_installed(attr_dict, mock_package_name, mock_path_to_package)

    assert len(result) == 2
    assert result[0]
    assert result[1].solution == ""


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
    assert "is not installed" in result[1].description

def test_valid_selftest_validate_selftestpy_file_exists(fx_copy_fn_main_mock_integration):

    attr_dict = sdk_validate_configs.selftest_attributes[2]

    path_selftest = os.path.join(mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_UTIL, "selftest.py")

    result = sdk_validate_helpers.selftest_validate_selftestpy_file_exists(attr_dict, path_selftest)

    assert len(result) == 2
    assert result[0]
    assert "selftest.py file found" in result[1].description

def test_invalid_selftest_validate_selftestpy_file_exists():

    attr_dict = sdk_validate_configs.selftest_attributes[2]

    path_selftest = "pacakge/with/no/util/selftest.py"

    result = sdk_validate_helpers.selftest_validate_selftestpy_file_exists(attr_dict, path_selftest)

    assert len(result) == 2
    assert result[0] is False
    assert "selftest.py is a required file" in result[1].description

def test_selftest_run_selftestpy_valid():

    attr_dict = sdk_validate_configs.selftest_attributes[3]

    package_name = "fake_package_name"

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.run_subprocess") as mock_subprocess:

        mock_subprocess.return_value = 0, "Success"

        result = sdk_validate_helpers.selftest_run_selftestpy(attr_dict, package_name)

        assert len(result) == 2
        assert result[0]
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_selftest_run_selftestpy_invalid(fx_copy_fn_main_mock_integration):

    attr_dict = sdk_validate_configs.selftest_attributes[3]

    package_name = "fake_package_name"

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.run_subprocess") as mock_subprocess:

        mock_subprocess.return_value = 1, "failure {'state': 'failure', 'reason': 'failed for test reasons'} and more text here..."

        result = sdk_validate_helpers.selftest_run_selftestpy(attr_dict, package_name)

        assert len(result) == 2
        assert result[0] is False
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
        assert "failed for test reasons" in result[1].description and package_name in result[1].description

def test_sefltest_run_selftestpy_rest_error(fx_copy_fn_main_mock_integration):

    attr_dict = sdk_validate_configs.selftest_attributes[3]

    package_name = "fake_package_name"

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.run_subprocess") as mock_subprocess:

        error_msg = u"ERROR: (fake) issue connecting to SOAR with some unicode: ล ฦ ว"
        mock_subprocess.return_value = 20, error_msg

        result = sdk_validate_helpers.selftest_run_selftestpy(attr_dict, package_name)

        assert len(result) == 2
        assert result[0] is False
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
        assert error_msg in result[1].description


def test_pass_package_files_manifest(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "MANIFEST.in"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1] # [i] is the index of the tuple, [1] is the attr_dict
    package_name = fx_copy_fn_main_mock_integration[0]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    # mock the get_close_matches method to return a match, which will pass the method
    with patch("resilient_sdk.util.sdk_validate_helpers.difflib.get_close_matches") as mock_close_matches:
        mock_close_matches.return_value = ["match"]

        result = sdk_validate_helpers.package_files_manifest(package_name, path_file, filename, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_fail_package_files_manifest(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "MANIFEST.in"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1] # [i] is the index of the tuple, [1] is the attr_dict
    package_name = fx_copy_fn_main_mock_integration[0]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    # mock the get_close_matches method to return an empty list, which will fail the method
    with patch("resilient_sdk.util.sdk_validate_helpers.difflib.get_close_matches") as mock_close_matches:
        mock_close_matches.return_value = []

        result = sdk_validate_helpers.package_files_manifest(package_name, path_file, filename, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_WARN

def test_pass_package_files_apikey_pem(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "apikey_permissions.txt"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    result = sdk_validate_helpers.package_files_apikey_pem(path_file, attr_dict)

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, SDKValidateIssue)
    assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_fail_package_files_apikey_pem(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "apikey_permissions.txt"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    # mock the file reading
    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.read_file") as mock_read_file:

        mock_read_file.return_value = ["#mock_commented_permissions\n", "mock_non_base_permission\n"]

        result = sdk_validate_helpers.package_files_apikey_pem(path_file, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL

def test_fail_package_files_template_match_dockerfile(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "Dockerfile"
    i = fx_get_package_files_config[filename]
    # because there are two Dockerfile tests, the first one will be at index i-1, the second one at index i
    attr_dict = sdk_validate_configs.package_files[i-1][1]
    package_name = fx_copy_fn_main_mock_integration[0]
    package_version = "fake.version"
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    # mock the get_close_matches method to return an empty list, which will fail the method
    with patch("resilient_sdk.util.sdk_validate_helpers.difflib.SequenceMatcher.ratio") as mock_ratio:
        mock_ratio.return_value = 0.2

        result = sdk_validate_helpers.package_files_template_match(package_name, package_version, path_file, filename, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_WARN

def test_pass_package_files_template_match_dockerfile(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "Dockerfile"
    i = fx_get_package_files_config[filename]
    # because there are two Dockerfile tests, the first one will be at index i-1, the second one at index i
    attr_dict = sdk_validate_configs.package_files[i-1][1]
    package_name = fx_copy_fn_main_mock_integration[0]
    package_version = "fake.version"
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    # mock the get_close_matches method to return an empty list, which will fail the method
    with patch("resilient_sdk.util.sdk_validate_helpers.difflib.SequenceMatcher.ratio") as mock_ratio:
        mock_ratio.return_value = 1.0

        result = sdk_validate_helpers.package_files_template_match(package_name, package_version, path_file, filename, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_pass_package_files_base_image_correct_dockerfile(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "Dockerfile"
    i = fx_get_package_files_config[filename]
    path_package = fx_copy_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(path_package,filename)
    with patch("resilient_sdk.util.package_file_helpers.parse_dockerfile") as mock_dict:
        mock_dict.return_value = {"FROM":[constants.DOCKER_BASE_REPO]}

        result = sdk_validate_helpers.package_files_validate_base_image(path_file, attr_dict, path_package)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_fail_package_files_base_image_old_dockerfile(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "Dockerfile"
    i = fx_get_package_files_config[filename]
    path_package = fx_copy_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(path_package,filename)
    with patch("resilient_sdk.util.package_file_helpers.parse_dockerfile") as mock_dict:
        mock_dict.return_value = {"FROM":[constants.DOCKER_BASE_REPO_OLD]}

        result = sdk_validate_helpers.package_files_validate_base_image(path_file, attr_dict, path_package)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL

def test_fail_package_files_base_image_incorrect_dockerfile(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "Dockerfile"
    i = fx_get_package_files_config[filename]
    path_package = fx_copy_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(path_package,filename)
    with patch("resilient_sdk.util.package_file_helpers.parse_dockerfile") as mock_dict:
        mock_dict.return_value = {"FROM":["incorrect_repo"]}

        result = sdk_validate_helpers.package_files_validate_base_image(path_file, attr_dict, path_package)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL


def test_fail_package_files_base_image_missing_dockerfile(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "Dockerfile"
    i = fx_get_package_files_config[filename]
    path_package = fx_copy_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(path_package,filename)
    with patch("resilient_sdk.util.package_file_helpers.parse_dockerfile") as mock_dict:
        mock_dict.return_value = {"FROM":[]}

        result = sdk_validate_helpers.package_files_validate_base_image(path_file, attr_dict, path_package)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL


def test_fail_package_files_base_image_too_many_dockerfile(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "Dockerfile"
    i = fx_get_package_files_config[filename]
    path_package = fx_copy_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(path_package,filename)
    with patch("resilient_sdk.util.package_file_helpers.parse_dockerfile") as mock_dict:
        mock_dict.return_value = {"FROM":[constants.DOCKER_BASE_REPO, constants.DOCKER_BASE_REPO]}

        result = sdk_validate_helpers.package_files_validate_base_image(path_file, attr_dict, path_package)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL

def test_fail_package_files_base_image_too_many_and_incorrect_dockerfile(fx_copy_fn_main_mock_integration, fx_get_package_files_config):
    filename = "Dockerfile"
    i = fx_get_package_files_config[filename]
    path_package = fx_copy_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(path_package,filename)
    with patch("resilient_sdk.util.package_file_helpers.parse_dockerfile") as mock_dict:
        mock_dict.return_value = {"FROM":["repo1", "repo2"]}

        result = sdk_validate_helpers.package_files_validate_base_image(path_file, attr_dict, path_package)

        assert len(result) == 2
        assert isinstance(result[0], SDKValidateIssue) and isinstance(result[1], SDKValidateIssue)
        assert result[0].severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL and result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL

def test_difflib_unified_diff_used_in_template_match():
    """A quick test to check that difflib.unified_diff works the same as when we wrote
    code that uses it. If this test fails, make sure that all logic using this difflib output format
    is updated to reflect that change in difflib. Specifically, check that
    package_file_helpers.color_diff_output is updated."""

    mock_fromfile_data = ["line 2"]
    mock_tofile_data = ["line 1"]

    diff = difflib.unified_diff(mock_fromfile_data, mock_tofile_data, n=0)

    # check that the lines are still the same that we'd expect when this was originally written
    for i, line in enumerate(diff):
        if i == 0:
            assert line.startswith("---")
        if i == 1:
            assert line.startswith("+++")
        if i == 2:
            assert line.startswith("@@ -1 +1 @@")

def test_pass_package_files_validate_config_py(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "config.py"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    # mock config parsing - return valid config
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_configs_from_config_py") as mock_config:

        mock_config.return_value = ("[fake_config]\nfake=fake", [{'name': 'fake', 'placeholder': 'fake'}])

        result = sdk_validate_helpers.package_files_validate_config_py(path_file, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG
        assert "fake=fake" in result.solution

def test_warn_package_files_validate_config_py(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "config.py"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    # mock config parsing - return no config
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_configs_from_config_py") as mock_config:

        mock_config.return_value = ("", [])

        result = sdk_validate_helpers.package_files_validate_config_py(path_file, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_INFO

def test_fail_package_files_validate_config_py(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "config.py"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    # mock config parsing - mock raising an exception
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_configs_from_config_py") as mock_config:

        mock_config.side_effect = SDKException("failed")

        result = sdk_validate_helpers.package_files_validate_config_py(path_file, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL

def test_pass_package_files_validate_customize_py(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "customize.py"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    # mock import def parsing - given a valid dict (actual validation of the import def happens)
    # in the get_import_definition_from_customize_py which is tested in
    # test_package_file_helpers.test_load_customize_py_module
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_import_definition_from_customize_py") as mock_config:

        mock_config.return_value = {"action_order": [], "actions": [ {} ]}

        result = sdk_validate_helpers.package_files_validate_customize_py(path_file, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_fail_package_files_validate_customize_py(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "customize.py"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    # mock import definition parsing - mock raising an exception
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_import_definition_from_customize_py") as mock_import_def:

        mock_import_def.side_effect = SDKException("failed")

        result = sdk_validate_helpers.package_files_validate_customize_py(path_file, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL

def test_package_files_validate_python_versions_in_scripts_fail(fx_copy_fn_main_mock_integration, fx_get_package_files_config):
    """test failure with all types of failure (and some success included)"""

    filename = "export.res"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i-1][1]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    # mock export.res
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_import_definition_from_customize_py") as mock_export_res:

        mock_export_res.return_value = {
            "scripts": [
                {
                    "language": "python",
                    "name": u"Shouldnt Pass Δ, Й, ק ,م, ๗, あ, 叶"
                },
                {
                    "language": "python3",
                    "name": u"Should Pass Δ, Й, ק ,م, ๗, あ, 叶"
                },
            ],
            "workflows": [{
                "name": u"Shouldnt Pass Δ, Й, ק ,م, ๗, あ, 叶",
                "content": {"xml":
                    "\u003c?xml version=\"1.0\" encoding=\"UTF-8\"?\u003e\u003c{\"multiselect_value\":[\"8b8b22d4-b20c-4d10-abac-a65211a5b9cd\",\"bf8e34a8-79aa-4ec4-b4c9-b8f1f0f7135e\"]}}},\"post_processing_script\":\"# post process of mock  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d workflow two\\n\\nincident.addNote(u\\\" \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d\\\")\",\"post_processing_script_language\":\"python\",\"pre_processing_script\":\"# A mock pre-process script for mock_workflow_one\\n\\ninputs.mock_input_number = 123\\ninputs.mock_input_boolean = True\\ninputs.mock_input_text = \\\"abc  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d abc\\\"\",\"pre_processing_script_language\":\"python\",\"result_name\":\"output_of_mock_function_one\"}\u003c/resilient:function\u003e\u003c/"
                }
            },{
                "name": u"Should Pass Δ, Й, ק ,م, ๗, あ, 叶",
                "content": {"xml":
                    "\u003c?xml version=\"1.0\" encoding=\"UTF-8\"?\u003e\u003c{\"multiselect_value\":[\"8b8b22d4-b20c-4d10-abac-a65211a5b9cd\",\"bf8e34a8-79aa-4ec4-b4c9-b8f1f0f7135e\"]}}},\"post_processing_script\":\"# post process of mock  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d workflow two\\n\\nincident.addNote(u\\\" \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d\\\")\",\"post_processing_script_language\":\"python3\",\"pre_processing_script\":\"# A mock pre-process script for mock_workflow_one\\n\\ninputs.mock_input_number = 123\\ninputs.mock_input_boolean = True\\ninputs.mock_input_text = \\\"abc  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d abc\\\"\",\"pre_processing_script_language\":\"python3\",\"result_name\":\"output_of_mock_function_one\"}\u003c/resilient:function\u003e\u003c/"
                }
            }],
            "playbooks": [{"display_name": "My PB", "local_scripts": [
                {
                    "language": "python",
                    "name": u"Shouldnt Pass Δ, Й, ק ,م, ๗, あ, 叶",
                },
                {
                    "language": "python3",
                    "name": u"Should Pass Δ, Й, ק ,م, ๗, あ, 叶",
                }]
            }]
        }

        results = sdk_validate_helpers.package_files_validate_script_python_versions(path_file, attr_dict)

        assert len(results) == 4
        result = results[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
        assert u"Global script 'Shouldnt Pass Δ, Й, ק ,م, ๗, あ, 叶' packaged with this app is written in Python 2" in result.description
        result = results[1]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
        assert u"Local script 'Shouldnt Pass Δ, Й, ק ,م, ๗, あ, 叶' in playbook 'My PB' packaged with this app is written in Python 2" in result.description
        result = results[2]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
        assert u"Pre-processing script for workflow 'Shouldnt Pass Δ, Й, ק ,م, ๗, あ, 叶' packaged with this app is written in Python 2" in result.description
        result = results[3]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
        assert u"Post-processing script for workflow 'Shouldnt Pass Δ, Й, ק ,م, ๗, あ, 叶' packaged with this app is written in Python 2" in result.description

@pytest.mark.parametrize("playbook_input", [
    [{"display_name": "My PB", "local_scripts":
       [{"language": "python3", "name": u"Should Pass Δ, Й, ק ,م, ๗, あ, 叶",}]}],
    [], # ensure empty playbook list works
    None # ensure None playbook object works
])
def test_package_files_validate_python_versions_in_scripts_pass(playbook_input, fx_copy_fn_main_mock_integration, fx_get_package_files_config):
    """add scripts everywhere they could be found, but make them all pass as py3 scripts"""

    filename = "export.res"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i-1][1]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    # mock export.res
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_import_definition_from_customize_py") as mock_export_res:

        mock_export_res.return_value = {
            "scripts": [{
                "language": "python3",
                "name": u"Should Pass Δ, Й, ק ,م, ๗, あ, 叶"
            },],
            "workflows": [{
                "name": u"Should Pass Δ, Й, ק ,م, ๗, あ, 叶",
                "content": {"xml":
                    "\u003c?xml version=\"1.0\" encoding=\"UTF-8\"?\u003e\u003c{\"multiselect_value\":[\"8b8b22d4-b20c-4d10-abac-a65211a5b9cd\",\"bf8e34a8-79aa-4ec4-b4c9-b8f1f0f7135e\"]}}},\"post_processing_script\":\"# post process of mock  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d workflow two\\n\\nincident.addNote(u\\\" \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d\\\")\",\"post_processing_script_language\":\"python3\",\"pre_processing_script\":\"# A mock pre-process script for mock_workflow_one\\n\\ninputs.mock_input_number = 123\\ninputs.mock_input_boolean = True\\ninputs.mock_input_text = \\\"abc  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d abc\\\"\",\"pre_processing_script_language\":\"python3\",\"result_name\":\"output_of_mock_function_one\"}\u003c/resilient:function\u003e\u003c/"
            }}],
            "playbooks": playbook_input
        }

        results = sdk_validate_helpers.package_files_validate_script_python_versions(path_file, attr_dict)

        assert len(results) == 1
        result = results[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG
        assert "Scripts in app use valid versions of Python" in result.description

@pytest.mark.parametrize("playbook_input, expected_severity", [
    ([{"display_name": "My PB",
        "activation_details": {
            "activation_conditions": {
                "conditions": [
                    {"field_name": "incident.properties.my_custom_field_1"}]}
        },
        "auto_cancelation_details": {
            "cancelation_conditions": {
                "conditions": [
                    {"field_name": "incident.properties.my_custom_field_2"}]}
        }
    }], SDKValidateIssue.SEVERITY_LEVEL_CRITICAL),
    ([{"display_name": "My PB",
        "activation_details": {
            "activation_conditions": {
                "conditions": [{"field_name": "incident.properties.my_custom_field_1"}]}
        }
    }], SDKValidateIssue.SEVERITY_LEVEL_CRITICAL),
    ([{"display_name": "My PB",
        "auto_cancelation_details": {
            "cancelation_conditions": {
                "conditions": [
                    {"field_name": "incident.properties.my_custom_field_2"}]}
        }
    }], SDKValidateIssue.SEVERITY_LEVEL_CRITICAL)
])
def test_validate_playbook_conditions_all_fields_included(playbook_input, expected_severity, fx_copy_fn_main_mock_integration, fx_get_package_files_config):
    filename = "export.res"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1]


    mock_export_res = {
        "fields": [],
        "playbooks": playbook_input
    }

    results = sdk_validate_helpers._validate_playbook_conditions_all_fields_included(mock_export_res, attr_dict, fx_copy_fn_main_mock_integration[0])

    assert len(results) == 1
    result = results[0]
    assert isinstance(result, SDKValidateIssue)
    assert result.severity == expected_severity

@pytest.mark.parametrize("playbook_input", [
    ([{"display_name": "My PB",
       "activation_details": {
            "activation_conditions": {
                "conditions": [
                    {"field_name": "task.id"}]}
        },
        "auto_cancelation_details": {
            "cancelation_conditions": {
                "conditions": [
                    {"field_name": "incident.id"}]}
        }
    }]),
    ([]),
    (None)
])
def test_validate_playbook_conditions_all_fields_included_no_issues(playbook_input, fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "export.res"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1]


    mock_export_res = {
        "fields": [],
        "playbooks": playbook_input
    }

    results = sdk_validate_helpers._validate_playbook_conditions_all_fields_included(mock_export_res, attr_dict, fx_copy_fn_main_mock_integration[0])

    assert len(results) == 0

def test_package_files_validate_no_playbook_dependencies_missing(fx_get_package_files_config):
    filename = "export.res"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1]

    # mock export.res
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_import_definition_from_customize_py") as mock_export_res:

        mock_export_res.return_value = {
            "fields": [],
            "playbooks": [{
                "activation_type": "manual",
                "display_name": "pb_test",
                "content": {
                    "content_version": 4,
                    "xml": u"\u003c?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?\u003e\u003cdefinitions xmlns=\"http://www.omg.org/spec/BPMN/20100524/MODEL\" xmlns:bpmndi=\"http://www.omg.org/spec/BPMN/20100524/DI\" xmlns:omgdc=\"http://www.omg.org/spec/DD/20100524/DC\" xmlns:omgdi=\"http://www.omg.org/spec/DD/20100524/DI\" xmlns:resilient=\"http://resilient.ibm.com/bpmn\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" targetNamespace=\"http://www.camunda.org/test\"\u003e\u003cprocess id=\"playbook_b28ea799_5c4b_44ae_9b59_e1c2318ae5a8\" isExecutable=\"true\" name=\"playbook_b28ea799_5c4b_44ae_9b59_e1c2318ae5a8\"\u003e\u003cdocumentation/\u003e\u003cstartEvent id=\"StartEvent_155asxm\"\u003e\u003coutgoing\u003eFlow_0mg86rd\u003c/outgoing\u003e\u003coutgoing\u003eFlow_1bc4xwb\u003c/outgoing\u003e\u003coutgoing\u003eFlow_17y1ve2\u003c/outgoing\u003e\u003coutgoing\u003eFlow_1itd994\u003c/outgoing\u003e\u003c/startEvent\u003e\u003cserviceTask id=\"ServiceTask_1\" name=\"mock_function_one\" resilient:type=\"function\"\u003e\u003cextensionElements\u003e\u003cresilient:function uuid=\"9b180887-4ff6-4d13-82a6-cb0a5d8718f1\"\u003e{\"inputs\":{\"49f10172-309a-4829-a5fe-1de71cdb4efb\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"number_value\":1}},\"01147ebf-ce3d-4cfb-814b-16145af4e511\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}},\"92eb3b7a-8859-4846-81a3-2995aec74bdb\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}},\"e40b9d9e-7ca1-45bc-913b-ce2a77e9b687\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"\"}},\"866625eb-8b46-4cc9-b713-cdfa548a1189\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_content_value\":{\"format\":\"unknown\",\"content\":\"\"}}},\"b6dfde6d-7516-4509-a5a2-54e72df9e0cd\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"select_value\":\"0a30d6ad-914a-47b1-83bf-c5667dbee974\"}},\"df7df8ba-cb65-4400-8290-070b155d28d4\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}},\"69dc0e78-a74b-4ccc-8d82-33b51780a569\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[\"8b8b22d4-b20c-4d10-abac-a65211a5b9cd\",\"bf8e34a8-79aa-4ec4-b4c9-b8f1f0f7135e\"]}}},\"result_name\":\"mf1\"}\u003c/resilient:function\u003e\u003c/extensionElements\u003e\u003cincoming\u003eFlow_0mg86rd\u003c/incoming\u003e\u003coutgoing\u003eFlow_1rmlnxf\u003c/outgoing\u003e\u003c/serviceTask\u003e\u003csequenceFlow id=\"Flow_0mg86rd\" sourceRef=\"StartEvent_155asxm\" targetRef=\"ServiceTask_1\"/\u003e\u003cendEvent id=\"EndPoint_2\" resilient:documentation=\"End point\"\u003e\u003cincoming\u003eFlow_0txnjrd\u003c/incoming\u003e\u003c/endEvent\u003e\u003csequenceFlow id=\"Flow_1rmlnxf\" sourceRef=\"ServiceTask_1\" targetRef=\"CollectionPoint_6\"/\u003e\u003cserviceTask id=\"ServiceTask_3\" name=\"mock_function_one\" resilient:type=\"function\"\u003e\u003cextensionElements\u003e\u003cresilient:function uuid=\"9b180887-4ff6-4d13-82a6-cb0a5d8718f1\"\u003e{\"inputs\":{\"49f10172-309a-4829-a5fe-1de71cdb4efb\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"number_value\":3}},\"01147ebf-ce3d-4cfb-814b-16145af4e511\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}},\"92eb3b7a-8859-4846-81a3-2995aec74bdb\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}},\"e40b9d9e-7ca1-45bc-913b-ce2a77e9b687\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"\"}},\"866625eb-8b46-4cc9-b713-cdfa548a1189\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_content_value\":{\"format\":\"unknown\",\"content\":\"\"}}},\"b6dfde6d-7516-4509-a5a2-54e72df9e0cd\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"select_value\":\"0a30d6ad-914a-47b1-83bf-c5667dbee974\"}},\"df7df8ba-cb65-4400-8290-070b155d28d4\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}},\"69dc0e78-a74b-4ccc-8d82-33b51780a569\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[\"8b8b22d4-b20c-4d10-abac-a65211a5b9cd\",\"bf8e34a8-79aa-4ec4-b4c9-b8f1f0f7135e\"]}}},\"result_name\":\"mf3\"}\u003c/resilient:function\u003e\u003c/extensionElements\u003e\u003cincoming\u003eFlow_1itd994\u003c/incoming\u003e\u003coutgoing\u003eFlow_1dl94rl\u003c/outgoing\u003e\u003c/serviceTask\u003e\u003cserviceTask id=\"ServiceTask_4\" name=\"mock_function_one\" resilient:type=\"function\"\u003e\u003cextensionElements\u003e\u003cresilient:function uuid=\"9b180887-4ff6-4d13-82a6-cb0a5d8718f1\"\u003e{\"inputs\":{\"49f10172-309a-4829-a5fe-1de71cdb4efb\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"number_value\":2}},\"01147ebf-ce3d-4cfb-814b-16145af4e511\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}},\"92eb3b7a-8859-4846-81a3-2995aec74bdb\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}},\"e40b9d9e-7ca1-45bc-913b-ce2a77e9b687\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"\"}},\"866625eb-8b46-4cc9-b713-cdfa548a1189\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_content_value\":{\"format\":\"unknown\",\"content\":\"\"}}},\"b6dfde6d-7516-4509-a5a2-54e72df9e0cd\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"select_value\":\"0a30d6ad-914a-47b1-83bf-c5667dbee974\"}},\"df7df8ba-cb65-4400-8290-070b155d28d4\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}},\"69dc0e78-a74b-4ccc-8d82-33b51780a569\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[\"8b8b22d4-b20c-4d10-abac-a65211a5b9cd\",\"bf8e34a8-79aa-4ec4-b4c9-b8f1f0f7135e\"]}}},\"result_name\":\"mf2\"}\u003c/resilient:function\u003e\u003c/extensionElements\u003e\u003cincoming\u003eFlow_17y1ve2\u003c/incoming\u003e\u003coutgoing\u003eFlow_1yx00x3\u003c/outgoing\u003e\u003c/serviceTask\u003e\u003cserviceTask id=\"ServiceTask_5\" name=\"mock_function_one\" resilient:type=\"function\"\u003e\u003cextensionElements\u003e\u003cresilient:function uuid=\"9b180887-4ff6-4d13-82a6-cb0a5d8718f1\"\u003e{\"inputs\":{\"49f10172-309a-4829-a5fe-1de71cdb4efb\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"number_value\":4}},\"01147ebf-ce3d-4cfb-814b-16145af4e511\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}},\"92eb3b7a-8859-4846-81a3-2995aec74bdb\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}},\"e40b9d9e-7ca1-45bc-913b-ce2a77e9b687\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"\"}},\"866625eb-8b46-4cc9-b713-cdfa548a1189\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_content_value\":{\"format\":\"unknown\",\"content\":\"\"}}},\"b6dfde6d-7516-4509-a5a2-54e72df9e0cd\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"select_value\":\"0a30d6ad-914a-47b1-83bf-c5667dbee974\"}},\"df7df8ba-cb65-4400-8290-070b155d28d4\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}},\"69dc0e78-a74b-4ccc-8d82-33b51780a569\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[\"8b8b22d4-b20c-4d10-abac-a65211a5b9cd\",\"bf8e34a8-79aa-4ec4-b4c9-b8f1f0f7135e\"]}}},\"result_name\":\"mf4\"}\u003c/resilient:function\u003e\u003c/extensionElements\u003e\u003cincoming\u003eFlow_1bc4xwb\u003c/incoming\u003e\u003coutgoing\u003eFlow_057wv06\u003c/outgoing\u003e\u003c/serviceTask\u003e\u003csequenceFlow id=\"Flow_1bc4xwb\" sourceRef=\"StartEvent_155asxm\" targetRef=\"ServiceTask_5\"/\u003e\u003csequenceFlow id=\"Flow_17y1ve2\" sourceRef=\"StartEvent_155asxm\" targetRef=\"ServiceTask_4\"/\u003e\u003csequenceFlow id=\"Flow_1itd994\" sourceRef=\"StartEvent_155asxm\" targetRef=\"ServiceTask_3\"/\u003e\u003cparallelGateway id=\"CollectionPoint_6\" resilient:documentation=\"Wait point\"\u003e\u003cincoming\u003eFlow_1rmlnxf\u003c/incoming\u003e\u003cincoming\u003eFlow_057wv06\u003c/incoming\u003e\u003cincoming\u003eFlow_1yx00x3\u003c/incoming\u003e\u003cincoming\u003eFlow_1dl94rl\u003c/incoming\u003e\u003coutgoing\u003eFlow_1s6hjr5\u003c/outgoing\u003e\u003c/parallelGateway\u003e\u003csequenceFlow id=\"Flow_1s6hjr5\" sourceRef=\"CollectionPoint_6\" targetRef=\"ScriptTask_7\"/\u003e\u003csequenceFlow id=\"Flow_057wv06\" sourceRef=\"ServiceTask_5\" targetRef=\"CollectionPoint_6\"/\u003e\u003csequenceFlow id=\"Flow_1yx00x3\" sourceRef=\"ServiceTask_4\" targetRef=\"CollectionPoint_6\"/\u003e\u003csequenceFlow id=\"Flow_1dl94rl\" sourceRef=\"ServiceTask_3\" targetRef=\"CollectionPoint_6\"/\u003e\u003cscriptTask id=\"ScriptTask_7\" name=\"Mock Incident Script\"\u003e\u003cextensionElements\u003e\u003cresilient:script uuid=\"52e88afe-0ca8-4bac-823f-980bc8ba2931\"/\u003e\u003c/extensionElements\u003e\u003cincoming\u003eFlow_1s6hjr5\u003c/incoming\u003e\u003coutgoing\u003eFlow_0txnjrd\u003c/outgoing\u003e\u003cscript\u003escript\u003c/script\u003e\u003c/scriptTask\u003e\u003csequenceFlow id=\"Flow_0txnjrd\" sourceRef=\"ScriptTask_7\" targetRef=\"EndPoint_2\"/\u003e\u003c/process\u003e\u003cbpmndi:BPMNDiagram id=\"BPMNDiagram_1\"\u003e\u003cbpmndi:BPMNPlane bpmnElement=\"playbook_b28ea799_5c4b_44ae_9b59_e1c2318ae5a8\" id=\"BPMNPlane_1\"\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_1dl94rl\" id=\"Flow_1dl94rl_di\"\u003e\u003comgdi:waypoint x=\"1180\" y=\"402\"/\u003e\u003comgdi:waypoint x=\"1180\" y=\"620\"/\u003e\u003comgdi:waypoint x=\"789\" y=\"620\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_1yx00x3\" id=\"Flow_1yx00x3_di\"\u003e\u003comgdi:waypoint x=\"950\" y=\"402\"/\u003e\u003comgdi:waypoint x=\"950\" y=\"620\"/\u003e\u003comgdi:waypoint x=\"789\" y=\"620\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_057wv06\" id=\"Flow_057wv06_di\"\u003e\u003comgdi:waypoint x=\"490\" y=\"402\"/\u003e\u003comgdi:waypoint x=\"490\" y=\"620\"/\u003e\u003comgdi:waypoint x=\"652\" y=\"620\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_1s6hjr5\" id=\"Flow_1s6hjr5_di\"\u003e\u003comgdi:waypoint x=\"721\" y=\"646\"/\u003e\u003comgdi:waypoint x=\"721\" y=\"738\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_1itd994\" id=\"Flow_1itd994_di\"\u003e\u003comgdi:waypoint x=\"814\" y=\"91\"/\u003e\u003comgdi:waypoint x=\"1180\" y=\"91\"/\u003e\u003comgdi:waypoint x=\"1180\" y=\"318\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_17y1ve2\" id=\"Flow_17y1ve2_di\"\u003e\u003comgdi:waypoint x=\"814\" y=\"91\"/\u003e\u003comgdi:waypoint x=\"950\" y=\"91\"/\u003e\u003comgdi:waypoint x=\"950\" y=\"318\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_1bc4xwb\" id=\"Flow_1bc4xwb_di\"\u003e\u003comgdi:waypoint x=\"627\" y=\"91\"/\u003e\u003comgdi:waypoint x=\"490\" y=\"91\"/\u003e\u003comgdi:waypoint x=\"490\" y=\"318\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_1rmlnxf\" id=\"Flow_1rmlnxf_di\"\u003e\u003comgdi:waypoint x=\"721\" y=\"402\"/\u003e\u003comgdi:waypoint x=\"721\" y=\"594\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_0mg86rd\" id=\"Flow_0mg86rd_di\"\u003e\u003comgdi:waypoint x=\"721\" y=\"117\"/\u003e\u003comgdi:waypoint x=\"721\" y=\"318\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_0txnjrd\" id=\"Flow_0txnjrd_di\"\u003e\u003comgdi:waypoint x=\"721\" y=\"822\"/\u003e\u003comgdi:waypoint x=\"721\" y=\"894\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNShape bpmnElement=\"StartEvent_155asxm\" id=\"StartEvent_155asxm_di\"\u003e\u003comgdc:Bounds height=\"52\" width=\"187.083\" x=\"627\" y=\"65\"/\u003e\u003cbpmndi:BPMNLabel\u003e\u003comgdc:Bounds height=\"0\" width=\"90\" x=\"616\" y=\"100\"/\u003e\u003c/bpmndi:BPMNLabel\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"ServiceTask_1\" id=\"ServiceTask_1_di\"\u003e\u003comgdc:Bounds height=\"84\" width=\"196\" x=\"623\" y=\"318\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"ServiceTask_3\" id=\"ServiceTask_3_di\"\u003e\u003comgdc:Bounds height=\"84\" width=\"196\" x=\"1082\" y=\"318\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"ServiceTask_4\" id=\"ServiceTask_4_di\"\u003e\u003comgdc:Bounds height=\"84\" width=\"196\" x=\"852\" y=\"318\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"ServiceTask_5\" id=\"ServiceTask_5_di\"\u003e\u003comgdc:Bounds height=\"84\" width=\"196\" x=\"392\" y=\"318\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"CollectionPoint_6\" id=\"CollectionPoint_6_di\"\u003e\u003comgdc:Bounds height=\"52\" width=\"137.13330000000002\" x=\"652\" y=\"594\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"EndPoint_2\" id=\"EndPoint_2_di\"\u003e\u003comgdc:Bounds height=\"52\" width=\"132.15\" x=\"655\" y=\"894\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"ScriptTask_7\" id=\"ScriptTask_7_di\"\u003e\u003comgdc:Bounds height=\"84\" width=\"196\" x=\"623\" y=\"737.5\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003c/bpmndi:BPMNPlane\u003e\u003c/bpmndi:BPMNDiagram\u003e\u003c/definitions\u003e"
                },
            }],
            "functions": []
        }

        results = sdk_validate_helpers.package_files_validate_no_playbook_dependencies_missing("fake/package/file", "fake/package", attr_dict)

        assert len(results) == 1
        result = results[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.description == "App includes playbook 'pb_test' which references function UUID(s) '9b180887-4ff6-4d13-82a6-cb0a5d8718f1, 9b180887-4ff6-4d13-82a6-cb0a5d8718f1, 9b180887-4ff6-4d13-82a6-cb0a5d8718f1, 9b180887-4ff6-4d13-82a6-cb0a5d8718f1' that are not included in the package"

def test_package_files_validate_found_unique_icon(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "app_logo.png"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path"))

    # mock import definition parsing - mock raising an exception
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_icon") as mock_icon:

        # making use of side_effect to change the behavior of the two calls this way
        # the "default" is not the same as the "icon"
        mock_icon.side_effect = ["1", "2"]

        result = sdk_validate_helpers.package_files_validate_icon(path_file, attr_dict, filename)

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, SDKValidateIssue)
    assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_package_files_validate_found_default_icon(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "app_logo.png"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path"))

    # mock import definition parsing - mock raising an exception
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_icon") as mock_icon:

        mock_icon.return_value = "" # this way both calls will return an empty string and thus be equal

        result = sdk_validate_helpers.package_files_validate_icon(path_file, attr_dict, filename)

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, SDKValidateIssue)
    assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_INFO
    assert "'{0}' is the default icon".format(filename) in result.description

def test_package_files_validate_improper_icon(fx_copy_fn_main_mock_integration, fx_get_package_files_config):

    filename = "app_logo.png"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path"))

    # mock import definition parsing - mock raising an exception
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_icon") as mock_icon:

        mock_icon.side_effect = SDKException("Failed for some reason")

        result = sdk_validate_helpers.package_files_validate_icon(path_file, attr_dict, filename)

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, SDKValidateIssue)
    assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    assert "ERROR: Failed for some reason" == result.description

def test_package_files_validate_license_is_default(fx_copy_fn_main_mock_integration,fx_get_package_files_config):

    filename = "LICENSE"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    result = sdk_validate_helpers.package_files_validate_license(path_file, attr_dict, filename)

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, SDKValidateIssue)
    assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    assert "'LICENSE' is the default license file" == result.description

def test_package_files_validate_license_is_not_default(fx_copy_fn_main_mock_integration,fx_get_package_files_config):

    filename = "LICENSE"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.read_file") as mock_read_file:

        mock_read_file.return_value = "A sample LICENSE\n\nThis should still be validated manually to ensure proper license type"

        result = sdk_validate_helpers.package_files_validate_license(path_file, attr_dict, filename)

    assert len(result) == 2
    assert isinstance(result[0], SDKValidateIssue)
    assert result[0].severity == SDKValidateIssue.SEVERITY_LEVEL_INFO
    assert "'LICENSE' file is valid" == result[0].description
    assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_package_files_validate_readme(fx_copy_fn_main_mock_integration,fx_get_package_files_config):

    filename = "README.md"
    i = fx_get_package_files_config[filename]
    attr_dict = sdk_validate_configs.package_files[i][1]
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    result = sdk_validate_helpers.package_files_validate_readme(fx_copy_fn_main_mock_integration[1], path_file, filename, attr_dict)

    assert len(result) == 1
    result = result[0]
    assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    assert "Cannot find one or more screenshots referenced in the README" in result.description

def test_payload_samples_empty(fx_copy_fn_main_mock_integration):
    # NOTE: if the payload samples ever change in the mock integration
    # this will need to be revisited

    mock_path_package = fx_copy_fn_main_mock_integration[1]
    func_name = "mock_function_two" # this one has empty JSON data
    attr_dict = sdk_validate_configs.payload_samples_attributes

    result = sdk_validate_helpers._validate_payload_samples(mock_path_package, func_name, attr_dict)

    assert isinstance(result, SDKValidateIssue)
    assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    assert "empty" in result.description
    assert "'output_json_example.json' and 'output_json_schema.json'" in result.description


def test_tox_tests_validate_tox_installed(fx_pip_install_tox):

    attr_dict = sdk_validate_configs.tests_attributes[0]

    result = sdk_validate_helpers.tox_tests_validate_tox_installed(attr_dict)

    assert result[0] == 1
    assert "'tox' was found in the Python environment" in result[1].description

def test_tox_tests_validate_tox_file_exists(fx_copy_fn_main_mock_integration):

    path_package = fx_copy_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.tests_attributes[1]

    result = sdk_validate_helpers.tox_tests_validate_tox_file_exists(path_package, attr_dict)

    assert result[0] == 1
    assert "'tox.ini' file was found in the package" in result[1].description

def test_TOX_MIN_ENV_VERSION_correct_format():
    # this method should help ensure that any changes to constants.TOX_MIN_ENV_VERSION
    # keep the correct format: py3[x] where [x] is the minor python version

    assert len(constants.TOX_MIN_ENV_VERSION) == 4
    assert constants.TOX_MIN_ENV_VERSION[:2] == "py"
    assert constants.TOX_MIN_ENV_VERSION[2] == "3"
    assert constants.TOX_MIN_ENV_VERSION[-1].isdigit()

def test_tox_tests_validate_min_env_version_only(fx_copy_fn_main_mock_integration):

    path_package = fx_copy_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.tests_attributes[2]

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.read_file") as mock_read_file:

        mock_read_file.return_value = ['[tox]\n', 'envlist = py36\n', 'skip_missing_interpreters=True\n', '\n', '\n', '[testenv:py36]\n', 'passenv=TEST_RESILIENT_*\n', 'commands = pytest -s {posargs}\n']

        result = sdk_validate_helpers.tox_tests_validate_min_env_version(path_package, attr_dict)

        assert result[0] == 1
        assert "Valid 'envlist=' was found in the 'tox.ini' file" in result[1].description

def test_tox_tests_validate_not_min_env_version_only(fx_copy_fn_main_mock_integration):

    path_package = fx_copy_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.tests_attributes[2]

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.read_file") as mock_read_file:

        mock_read_file.return_value = ['[tox]\n', 'envlist = py27,py36,py39\n', 'skip_missing_interpreters=True\n', '\n', '\n', '[testenv:py27]\n', 'passenv=TEST_RESILIENT_*\n', 'commands = pytest -s {posargs}\n']

        result = sdk_validate_helpers.tox_tests_validate_min_env_version(path_package, attr_dict)

        assert result[0] == 1
        assert "Unsupported tox environment found in envlist in 'tox.ini' file" in result[1].description

def test_tox_tests_run_tox_tests(fx_copy_fn_main_mock_integration, caplog):

    path_package = fx_copy_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.tests_attributes[3]

    # want to skip using a conftest file as that is irrelevant here
    args = constants.TOX_TESTS_DEFAULT_ARGS.append("--noconftest")

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.run_subprocess") as mock_tox_sub_process:

        mock_tox_sub_process.return_value = (None, "bad run")

        result = sdk_validate_helpers.tox_tests_run_tox_tests(path_package, attr_dict, args, None)

        assert "Using mock args" in caplog.text
        assert "'-m', 'not livetest'" in caplog.text
        assert "Something went wrong..." in result[1].description
        assert "bad run" in result[1].description
        assert result[0] == 0

def test_tox_tests_run_tox_tests_with_pytest_args(fx_copy_fn_main_mock_integration, caplog):

    path_package = fx_copy_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.tests_attributes[3]

    args = ["m=\"not livetest\"", "resilienthost=\"fake.soar.com\""]

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.run_subprocess") as mock_tox_sub_process:

        mock_tox_sub_process.return_value = (None, "bad run")

        result = sdk_validate_helpers.tox_tests_run_tox_tests(path_package, attr_dict, args, None)

        assert "Reading tox args from command line flag --tox-args" in caplog.text
        assert result[0] == 0

def test_tox_tests_run_tox_tests_with_settings_file(fx_copy_fn_main_mock_integration, caplog):

    path_package = fx_copy_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.tests_attributes[3]

    settings_file_path = mock_paths.MOCK_SDK_SETTINGS_PATH

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.run_subprocess") as mock_tox_sub_process:

        mock_tox_sub_process.return_value = (None, "bad run")

        result = sdk_validate_helpers.tox_tests_run_tox_tests(path_package, attr_dict, None, settings_file_path)

        assert "Reading tox args from sdk settings JSON file" in caplog.text
        assert result[0] == 0


def test_tox_tests_parse_xml_report():

    results = sdk_validate_helpers._tox_tests_parse_xml_report(mock_paths.MOCK_PYTEST_XML_REPORT_PATH)

    assert len(results) == 5
    assert results[0] == 2
    assert results[1] == 1
    assert results[2] == 0
    assert results[3] == ""
    assert results[4] == u'record_property = <function record_property.<locals>.append_property\n                at 0x000001A1A9EB40D0>\n\n                def test_fails(record_property):\n                record_property("key", u"value2 some unicode: Δ, Й, ק ,م, ๗, あ, 叶")\n                > assert 1 == 2\n                E assert 1 == 2\n\n                test_something.py:8: AssertionError\n            \n\n---\n\n'


def test_pylint_validate_pylint_is_installed():

    attr_dict = sdk_validate_configs.pylint_attributes[0]

    result = sdk_validate_helpers.pylint_validate_pylint_installed(attr_dict=attr_dict)

    assert len(result) == 2
    assert result[0] == 1
    assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG


def test_pylint_validate_pylint_not_installed():

    attr_dict = sdk_validate_configs.pylint_attributes[0]

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.get_package_version") as mock_pylint_version:

        mock_pylint_version.return_value = None

        result = sdk_validate_helpers.pylint_validate_pylint_installed(attr_dict=attr_dict)

        assert len(result) == 2
        assert result[0] == -1 # validate is skipped
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_INFO


def test_pylint_run_pylint_scan_success(fx_copy_fn_main_mock_integration):

    package_name = fx_copy_fn_main_mock_integration[0]
    path_package = fx_copy_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.pylint_attributes[1]

    with patch("resilient_sdk.util.sdk_validate_helpers.lint.Run") as mock_pylint_run:
        with patch("resilient_sdk.util.sdk_validate_helpers.StringIO") as mock_string_io:

            run = mock_pylint_run.return_value

            # because the objects are different in py2 vs py3,
            # mocks have to be similarly different
            if sys.version_info.major >= 3:
                run.linter.stats.global_note = 10
                run.linter.stats.info = 0
                run.linter.stats.refactor = 0
                run.linter.stats.convention = 0
                run.linter.stats.warning = 0
                run.linter.stats.error = 0
                run.linter.stats.fatal = 0
            else:
                run.linter.stats = {
                    "global_note": 10,
                    "info": 0,
                    "refactor": 0,
                    "convention": 0,
                    "warning": 0,
                    "error": 0,
                    "fatal": 0,
                }
            mock_string_io.return_value.getvalue.return_value = "Mock pylint report"

            result = sdk_validate_helpers.pylint_run_pylint_scan(
                path_package=path_package,package_name=package_name,
                attr_dict=attr_dict,path_sdk_settings=None)

            assert len(result) == 2
            assert result[0] == 1
            assert "Pylint scan passed" in result[1].description


def test_pylint_run_pylint_scan_failure(fx_copy_fn_main_mock_integration):

    package_name = fx_copy_fn_main_mock_integration[0]
    path_package = fx_copy_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.pylint_attributes[1]

    with patch("resilient_sdk.util.sdk_validate_helpers.lint.Run") as mock_pylint_run:
        with patch("resilient_sdk.util.sdk_validate_helpers.StringIO") as mock_string_io:

            run = mock_pylint_run.return_value

            if sys.version_info.major >= 3:
                run.linter.stats.global_note = 3.4
                run.linter.stats.info = 0
                run.linter.stats.refactor = 0
                run.linter.stats.convention = 0
                run.linter.stats.warning = 3
                run.linter.stats.error = 1
                run.linter.stats.fatal = 0
            else:
                run.linter.stats = {
                    "global_note": 3.4,
                    "info": 0,
                    "refactor": 0,
                    "convention": 0,
                    "warning": 3,
                    "error": 1,
                    "fatal": 0,
                }
            mock_string_io.return_value.getvalue.return_value = "Mock pylint report"

            result = sdk_validate_helpers.pylint_run_pylint_scan(
                path_package=path_package,package_name=package_name,
                attr_dict=attr_dict,path_sdk_settings=None)

            assert len(result) == 2
            assert result[0] == 0
            assert "The Pylint score was 3.40/10" in result[1].description


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="requires python3.6 or higher")
def test_bandit_validate_bandit_is_installed():

    attr_dict = sdk_validate_configs.bandit_attributes[0]

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.get_package_version") as mock_bandit_version:

        mock_bandit_version.return_value = "0.0.0"

        result = sdk_validate_helpers.bandit_validate_bandit_installed(attr_dict=attr_dict)

        assert len(result) == 2
        assert result[0] == 1
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="requires python3.6 or higher")
def test_bandit_validate_bandit_not_installed():

    attr_dict = sdk_validate_configs.bandit_attributes[0]

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.get_package_version") as mock_bandit_version:

        mock_bandit_version.return_value = None

        result = sdk_validate_helpers.bandit_validate_bandit_installed(attr_dict=attr_dict)

        assert len(result) == 2
        assert result[0] == -1
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_INFO


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="requires python3.6 or higher")
def test_bandit_run_bandit_scan_success(fx_pip_install_bandit, fx_copy_fn_main_mock_integration, caplog):

    package_name = fx_copy_fn_main_mock_integration[0]
    path_package = fx_copy_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.bandit_attributes[1]

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.run_subprocess") as mock_bandit_subprocess:

        mock_bandit_subprocess.return_value = (0, "Success")

        result = sdk_validate_helpers.bandit_run_bandit_scan(path_package=path_package, attr_dict=attr_dict, package_name=package_name)

        assert len(result) == 2
        assert result[0] == 1
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_INFO

@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="requires python3.6 or higher")
def test_bandit_run_bandit_scan_fails(fx_pip_install_bandit, fx_copy_fn_main_mock_integration, caplog):

    package_name = fx_copy_fn_main_mock_integration[0]
    path_package = fx_copy_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.bandit_attributes[1]

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.run_subprocess") as mock_bandit_subprocess:

        mock_bandit_subprocess.return_value = (1, "Test results: Failed")

        result = sdk_validate_helpers.bandit_run_bandit_scan(path_package=path_package, attr_dict=attr_dict, package_name=package_name)

        assert len(result) == 2
        assert result[0] == 0
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
