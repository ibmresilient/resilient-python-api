#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import os
import sys
import shutil
from resilient_sdk.cmds import base_cmd, CmdCodegen
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util import package_file_helpers as package_helpers
from tests.unit import helpers
from tests.shared_mock_data import mock_paths

EXPECTED_FILES_ROOT_DIR = [
    'Dockerfile',
    'MANIFEST.in',
    'README.md',
    'apikey_permissions.txt',
    'data',
    'doc',
    'entrypoint.sh',
    'fn_main_mock_integration',
    'icons',
    'payload_samples',
    'setup.py',
    'tests',
    'tox.ini'
]

EXPECTED_FILES_DATA_DIR = ['wf_mock_workflow_one.md', 'wf_mock_workflow_two.md']
EXPECTED_FILES_DOC_DIR = ['screenshots']
EXPECTED_FILES_DOC_SCREENSHOTS_DIR = ['main.png']
EXPECTED_FILES_PACKAGE_DIR = ['LICENSE', '__init__.py', 'components', 'util']
EXPECTED_FILES_PACKAGE_COMPONENTS_DIR = ['__init__.py', 'funct_mock_function_one.py', 'funct_mock_function_two.py']
EXPECTED_FILES_PACKAGE_UTIL_DIR = ['__init__.py', 'config.py', 'customize.py', 'data', 'selftest.py']
EXPECTED_FILES_PACKAGE_UTIL_DATA_DIR = ['export.res']
EXPECTED_FILES_ICONS_DIR = ['app_logo.png', 'company_logo.png']
EXPECTED_FILES_TESTS_DIR = ['test_funct_mock_function_one.py', 'test_funct_mock_function_two.py']
EXPECTED_FILES_PAYLOAD_SAMPLES_DIR = ['mock_function_one', 'mock_function_two']
EXPECTED_FILES_PAYLOAD_SAMPLES_FN_NAME_DIR = ['mock_json_endpoint_fail.json', 'mock_json_endpoint_success.json', 'mock_json_expectation_fail.json',
                                              'mock_json_expectation_success.json', 'output_json_example.json', 'output_json_schema.json']


def general_test_package_structure(package_name, package_path):
    """
    This is a general function that the tests for gen_package and reload_package
    call to make sure that the expected files are created in each directory
    """
    assert helpers.verify_expected_list(EXPECTED_FILES_ROOT_DIR, os.listdir(package_path))
    assert helpers.verify_expected_list(EXPECTED_FILES_DATA_DIR, os.listdir(os.path.join(package_path, "data")))
    assert helpers.verify_expected_list(EXPECTED_FILES_DOC_DIR, os.listdir(os.path.join(package_path, "doc")))
    assert helpers.verify_expected_list(EXPECTED_FILES_DOC_SCREENSHOTS_DIR, os.listdir(os.path.join(package_path, "doc", "screenshots")))
    assert helpers.verify_expected_list(EXPECTED_FILES_PACKAGE_DIR, os.listdir(os.path.join(package_path, package_name)))
    assert helpers.verify_expected_list(EXPECTED_FILES_PACKAGE_COMPONENTS_DIR, os.listdir(os.path.join(package_path, package_name, "components")))
    assert helpers.verify_expected_list(EXPECTED_FILES_PACKAGE_UTIL_DIR, os.listdir(os.path.join(package_path, package_name, "util")))
    assert helpers.verify_expected_list(EXPECTED_FILES_PACKAGE_UTIL_DATA_DIR, os.listdir(os.path.join(package_path, package_name, "util", "data")))
    assert helpers.verify_expected_list(EXPECTED_FILES_ICONS_DIR, os.listdir(os.path.join(package_path, "icons")))
    assert helpers.verify_expected_list(EXPECTED_FILES_TESTS_DIR, os.listdir(os.path.join(package_path, "tests")))

    # Test payload_samples were generated for each fn
    files_in_payload_samples = sorted(os.listdir(os.path.join(package_path, "payload_samples")))
    assert helpers.verify_expected_list(EXPECTED_FILES_PAYLOAD_SAMPLES_DIR, files_in_payload_samples)

    for file_name in files_in_payload_samples:
        assert helpers.verify_expected_list(EXPECTED_FILES_PAYLOAD_SAMPLES_FN_NAME_DIR, os.listdir(os.path.join(package_path, "payload_samples", file_name)))


def test_gen_package(fx_get_sub_parser, fx_cmd_line_args_codegen_package, fx_mk_temp_dir):
    """
    This tests that when a package is generated with codegen
    that each of the EXPECTED_FILES exist in each directory.
    This test is NOT concerned about the contents of each file,
    just that it exists
    """
    output_path = mock_paths.TEST_TEMP_DIR

    # Add paths to an output base and an export.res file
    sys.argv.extend(["-o", output_path])
    # sys.argv.extend(["-e", mock_paths.MOCK_EXPORT_RES])

    cmd_codegen = CmdCodegen(fx_get_sub_parser)
    args = cmd_codegen.parser.parse_known_args()[0]
    cmd_codegen._gen_package(args)

    package_name = args.package
    package_path = os.path.join(output_path, args.package)
    general_test_package_structure(package_name, package_path)
