#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import difflib
import os
import sys

import pkg_resources
import pytest
from mock import patch
from resilient_sdk.util import (constants, sdk_validate_configs,
                                sdk_validate_helpers)
from resilient_sdk.util.sdk_exception import SDKException
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
    
def test_sefltest_run_selftestpy_valid():

    attr_dict = sdk_validate_configs.selftest_attributes[3]

    package_name = "fake_package_name"

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.run_subprocess") as mock_subprocess:
        
        mock_subprocess.return_value = 0, "Success"

        result = sdk_validate_helpers.selftest_run_selftestpy(attr_dict, package_name)

        assert len(result) == 2
        assert result[0]
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_sefltest_run_selftestpy_invalid(fx_copy_fn_main_mock_integration):

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

def test_pass_package_files_manifest(fx_copy_fn_main_mock_integration):

    filename = "MANIFEST.in"
    attr_dict = sdk_validate_configs.package_files.get(filename)
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

def test_fail_package_files_manifest(fx_copy_fn_main_mock_integration):

    filename = "MANIFEST.in"
    attr_dict = sdk_validate_configs.package_files.get(filename)
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

def test_pass_package_files_apikey_pem(fx_copy_fn_main_mock_integration):

    filename = "apikey_permissions.txt"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    result = sdk_validate_helpers.package_files_apikey_pem(path_file, attr_dict)

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, SDKValidateIssue)
    assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_fail_package_files_apikey_pem(fx_copy_fn_main_mock_integration):

    filename = "apikey_permissions.txt"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    # mock the file reading
    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.read_file") as mock_read_file:

        mock_read_file.return_value = ["#mock_commented_permissions\n", "mock_non_base_permission\n"]

        result = sdk_validate_helpers.package_files_apikey_pem(path_file, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL

def test_fail_package_files_template_match_dockerfile(fx_copy_fn_main_mock_integration):

    filename = "Dockerfile"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    package_name = fx_copy_fn_main_mock_integration[0]
    package_version = "fake.version"
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    # mock the get_close_matches method to return an empty list, which will fail the method
    with patch("resilient_sdk.util.sdk_validate_helpers.difflib.SequenceMatcher.ratio") as mock_ratio:
        mock_ratio.return_value = 0.0

        result = sdk_validate_helpers.package_files_template_match(package_name, package_version, path_file, filename, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_WARN

def test_pass_package_files_template_match_dockerfile(fx_copy_fn_main_mock_integration):

    filename = "Dockerfile"
    attr_dict = sdk_validate_configs.package_files.get(filename)
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

def test_fail_package_files_template_match_entrypoint(fx_copy_fn_main_mock_integration):

    filename = "entrypoint.sh"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    package_name = fx_copy_fn_main_mock_integration[0]
    package_version = "fake.version"
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    # mock the get_close_matches method to return an empty list, which will fail the method
    with patch("resilient_sdk.util.sdk_validate_helpers.difflib.SequenceMatcher.ratio") as mock_ratio:
        mock_ratio.return_value = 0.0

        result = sdk_validate_helpers.package_files_template_match(package_name, package_version, path_file, filename, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_WARN

def test_pass_package_files_template_match_entrypoint(fx_copy_fn_main_mock_integration):

    filename = "entrypoint.sh"
    attr_dict = sdk_validate_configs.package_files.get(filename)
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

def test_pass_package_files_validate_config_py(fx_copy_fn_main_mock_integration):
    
    filename = "config.py"
    attr_dict = sdk_validate_configs.package_files.get(filename)
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

def test_warn_package_files_validate_config_py(fx_copy_fn_main_mock_integration):
    
    filename = "config.py"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    # mock config parsing - return no config
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_configs_from_config_py") as mock_config:

        mock_config.return_value = ("", [])

        result = sdk_validate_helpers.package_files_validate_config_py(path_file, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_INFO

def test_fail_package_files_validate_config_py(fx_copy_fn_main_mock_integration):
    
    filename = "config.py"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    # mock config parsing - mock raising an exception
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_configs_from_config_py") as mock_config:

        mock_config.side_effect = SDKException("failed")

        result = sdk_validate_helpers.package_files_validate_config_py(path_file, attr_dict)

        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL

def test_pass_package_files_validate_customize_py(fx_copy_fn_main_mock_integration):
    
    filename = "customize.py"
    attr_dict = sdk_validate_configs.package_files.get(filename)
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

def test_fail_package_files_validate_customize_py(fx_copy_fn_main_mock_integration):
    
    filename = "customize.py"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    # mock import definition parsing - mock raising an exception
    with patch("resilient_sdk.util.sdk_validate_helpers.package_helpers.get_import_definition_from_customize_py") as mock_import_def:

        mock_import_def.side_effect = SDKException("failed")

        result = sdk_validate_helpers.package_files_validate_customize_py(path_file, attr_dict)
        
        assert len(result) == 1
        result = result[0]
        assert isinstance(result, SDKValidateIssue)
        assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL

def test_package_files_validate_found_unique_icon(fx_copy_fn_main_mock_integration):

    filename = "app_logo.png"
    attr_dict = sdk_validate_configs.package_files.get(filename)
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

def test_package_files_validate_found_default_icon(fx_copy_fn_main_mock_integration):

    filename = "app_logo.png"
    attr_dict = sdk_validate_configs.package_files.get(filename)
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

def test_package_files_validate_improper_icon(fx_copy_fn_main_mock_integration):

    filename = "app_logo.png"
    attr_dict = sdk_validate_configs.package_files.get(filename)
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

def test_package_files_validate_license_is_default(fx_copy_fn_main_mock_integration):

    filename = "LICENSE"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    result = sdk_validate_helpers.package_files_validate_license(path_file, attr_dict, filename)

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, SDKValidateIssue)
    assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    assert "'LICENSE' is the default license file" == result.description

def test_package_files_validate_license_is_not_default(fx_copy_fn_main_mock_integration):

    filename = "LICENSE"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], attr_dict.get("path").format(fx_copy_fn_main_mock_integration[0]))

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.setup_env_and_render_jinja_file") as mock_jinja_render:

        mock_jinja_render.return_value = "A sample LICENSE\n\nThis should still be validated manually to ensure proper license type"

        result = sdk_validate_helpers.package_files_validate_license(path_file, attr_dict, filename)

    assert len(result) == 2
    assert isinstance(result[0], SDKValidateIssue)
    assert result[0].severity == SDKValidateIssue.SEVERITY_LEVEL_INFO
    assert "'LICENSE' file is valid" == result[0].description
    assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG

def test_package_files_validate_readme(fx_copy_fn_main_mock_integration):

    filename = "README.md"
    attr_dict = sdk_validate_configs.package_files.get(filename)
    path_file = os.path.join(fx_copy_fn_main_mock_integration[1], filename)

    result = sdk_validate_helpers.package_files_validate_readme(fx_copy_fn_main_mock_integration[1], path_file, filename, attr_dict)

    assert len(result) == 1
    result = result[0]
    assert result.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
    assert "Cannot find the following screenshot(s) referenced in the README" in result.description

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
        assert "Unsupported tox env found in envlist in 'tox.ini' file" in result[1].description

def test_tox_tests_run_tox_tests(fx_pip_install_tox, fx_copy_and_pip_install_fn_main_mock_integration, caplog):

    path_package = fx_copy_and_pip_install_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.tests_attributes[3]

    # want to skip using a conftest file as that is irrelevant here
    args = constants.TOX_TESTS_DEFAULT_ARGS.append("--noconftest")

    result = sdk_validate_helpers.tox_tests_run_tox_tests(path_package, attr_dict, args, None)

    assert "Using mock args" in caplog.text
    assert result[0] == 1


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

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.get_package_version") as mock_pylint_version:

        mock_pylint_version.return_value = "0.0.0"

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


def test_bandit_validate_bandit_is_installed():

    attr_dict = sdk_validate_configs.bandit_attributes[0]

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.get_package_version") as mock_bandit_version:

        mock_bandit_version.return_value = "0.0.0"

        result = sdk_validate_helpers.bandit_validate_bandit_installed(attr_dict=attr_dict)

        assert len(result) == 2
        assert result[0] == 1
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_DEBUG


def test_bandit_validate_bandit_not_installed():

    attr_dict = sdk_validate_configs.bandit_attributes[0]

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.get_package_version") as mock_bandit_version:

        mock_bandit_version.return_value = None

        result = sdk_validate_helpers.bandit_validate_bandit_installed(attr_dict=attr_dict)

        assert len(result) == 2
        assert result[0] == -1
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_INFO


def test_bandit_run_bandit_scan_success(fx_pip_install_bandit, fx_copy_and_pip_install_fn_main_mock_integration, caplog):

    package_name = fx_copy_and_pip_install_fn_main_mock_integration[0]
    path_package = fx_copy_and_pip_install_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.bandit_attributes[1]

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.run_subprocess") as mock_bandit_subprocess:

        mock_bandit_subprocess.return_value = (0, "Success")

        result = sdk_validate_helpers.bandit_run_bandit_scan(path_package=path_package, attr_dict=attr_dict, package_name=package_name)

        assert len(result) == 2
        assert result[0] == 1
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_INFO


def test_bandit_run_bandit_scan_fails(fx_pip_install_bandit, fx_copy_and_pip_install_fn_main_mock_integration, caplog):

    package_name = fx_copy_and_pip_install_fn_main_mock_integration[0]
    path_package = fx_copy_and_pip_install_fn_main_mock_integration[1]
    attr_dict = sdk_validate_configs.bandit_attributes[1]

    with patch("resilient_sdk.util.sdk_validate_helpers.sdk_helpers.run_subprocess") as mock_bandit_subprocess:

        mock_bandit_subprocess.return_value = (1, "Test results: Failed")

        result = sdk_validate_helpers.bandit_run_bandit_scan(path_package=path_package, attr_dict=attr_dict, package_name=package_name)

        assert len(result) == 2
        assert result[0] == 0
        assert result[1].severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL
