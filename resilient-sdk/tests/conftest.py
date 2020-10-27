#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

"""
Shared pytest fixtures

Note:
    -   Code after the 'yield' statement in a fixture
        is ran after the test (or scope i.e. test session) has complete
    -   fx_ prefixes a 'fixture'
    -   Put fixture logic in separate 'private' function so we
        can share logic between fixtures
    -   Fixture must have BEFORE and AFTER docstring
"""

import copy
import sys
import os
import shutil
import pytest
import resilient_sdk.app as app
from resilient_sdk.util import sdk_helpers
from tests.shared_mock_data import mock_paths


def _mk_temp_dir():
    if os.path.exists(mock_paths.TEST_TEMP_DIR):
        shutil.rmtree(mock_paths.TEST_TEMP_DIR)

    os.makedirs(mock_paths.TEST_TEMP_DIR)


def _rm_temp_dir():
    if os.path.exists(mock_paths.TEST_TEMP_DIR):
        shutil.rmtree(mock_paths.TEST_TEMP_DIR)


def _mk_app_config():
    write_path = os.path.join(mock_paths.TEST_TEMP_DIR, "app.config")
    resilient_mock = "{0}.{1}".format(os.path.join(mock_paths.SHARED_MOCK_DATA_DIR, "resilient_api_mock"), "ResilientAPIMock")

    app_configs = """
[resilient]
#api_key_id=xxx
#api_key_secret=xxx

host=192.168.56.1
port=443
org=Test Organization
email=integrations@example.com
password=PassWord_;)

#componentsdir=~/.resilient/components
logdir=~/.resilient/logs/
logfile=app.log
loglevel=DEBUG

cafile=false

resilient_mock={0}""".format(resilient_mock)

    sdk_helpers.write_file(write_path, app_configs)

    return write_path


def _add_to_cmd_line_args(args_to_add):
    sys.argv.extend(args_to_add)


@pytest.fixture(scope="session")
def fx_mock_res_client():
    """
    Before: Creates a mock instance of res_client
    After: Removes temp directory used to store temp app.config
    """
    _mk_temp_dir()
    app_config = _mk_app_config()

    yield sdk_helpers.get_resilient_client(path_config_file=app_config)
    _rm_temp_dir()


@pytest.fixture
def fx_mk_temp_dir():
    """
    Before: Creates a directory at mock_paths.TEST_TEMP_DIR
    After: Removes the directory
    """
    _mk_temp_dir()
    yield
    _rm_temp_dir()


@pytest.fixture
def fx_mk_app_config():
    """
    Before: Writes the app_configs text to an app.config file in the TEST_TEMP_DIR
    After: Nothing (mk_temp_dir will clean up)
    Note: MUST be called AFTER mk_temp_dir
    """
    return _mk_app_config()


@pytest.fixture
def fx_copy_fn_main_mock_integration():
    """
    Before: Creates temp dir and copies fn_main_mock_integration to it
    Returns a tuple (mock_integration_name, path_fn_main_mock_integration)
    After: Removes the temp directory
    """
    _mk_temp_dir()
    mock_integration_name = "fn_main_mock_integration"
    path_fn_main_mock_integration = os.path.join(mock_paths.TEST_TEMP_DIR, mock_integration_name)
    shutil.copytree(mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION, path_fn_main_mock_integration)
    yield (mock_integration_name, path_fn_main_mock_integration)
    _rm_temp_dir()


@pytest.fixture
def fx_cmd_line_args_codegen_package():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "codegen",
        "-p", "fn_main_mock_integration",
        "-m", "fn_main_mock_integration",
        "-f", "mock_function_one",
        "--rule", "Mock Manual Rule", "Mock: Auto Rule", "Mock Task Rule", "Mock Script Rule", "Mock Manual Rule Message Destination",
        "--workflow", "mock_workflow_one", "mock_workflow_two",
        "--field", "mock_field_number", "mock_field_number", "mock_field_text_area",
        "--artifacttype", "mock_artifact_2", "mock_artifact_type_one",
        "--datatable", "mock_data_table",
        "--task", "mock_custom_task_one", "mock_cusom_task__________two",
        "--script", "Mock Script One"
    ]

    _add_to_cmd_line_args(args_to_add)

    yield

    sys.argv = original_cmd_line


@pytest.fixture
def fx_cmd_line_args_package():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "package",
        "-p", "fn_main_mock_integration"
    ]

    _add_to_cmd_line_args(args_to_add)

    yield

    sys.argv = original_cmd_line


@pytest.fixture
def fx_cmd_line_args_docgen():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "docgen",
        "-p", "fn_main_mock_integration",
    ]

    _add_to_cmd_line_args(args_to_add)

    yield

    sys.argv = original_cmd_line

@pytest.fixture
def fx_cmd_line_args_clone_typechange():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers

    Sets 2 args for clone, a workflow to clone and a new type for the workflow
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "clone",
        "-w", "mock_workflow_two", "mock_cloned_workflow",
        "-type", "task"
    ]

    _add_to_cmd_line_args(args_to_add)

    yield

    sys.argv = original_cmd_line

@pytest.fixture
def fx_cmd_line_args_clone_prefix():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers

    Sets 2 args for clone, a workflow to clone and a new type for the workflow
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "clone",
        "-w", "mock_workflow_two", "mock_workflow_one",
        "-m", "fn_main_mock_integration",
        "-f", "mock_function_one",
        "--rule", "Mock Manual Rule", "Mock: Auto Rule", "Mock Task Rule", "Mock Script Rule", "Mock Manual Rule Message Destination",
        "-pre", "v2"
    ]

    _add_to_cmd_line_args(args_to_add)

    yield

    sys.argv = original_cmd_line



@pytest.fixture
def fx_cmd_line_args_dev_set_version():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "dev",
        "-p", "fn_main_mock_integration",
        "--set-version", "35.0.0"
    ]

    _add_to_cmd_line_args(args_to_add)

    yield

    sys.argv = original_cmd_line


@pytest.fixture
def fx_cmd_line_args_dev_set_bad_version():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "dev",
        "-p", "fn_main_mock_integration",
        "--set-version", "35.x.0"
    ]

    _add_to_cmd_line_args(args_to_add)

    yield

    sys.argv = original_cmd_line


@pytest.fixture(scope="session")
def fx_get_sub_parser():
    """
    Before: Return a main_parser setup with sub_parser added
    After: Nothing
    """
    main_parser = app.get_main_app_parser()
    sub_parser = app.get_main_app_sub_parser(main_parser)
    return sub_parser
