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
import logging
import os
import shutil
import sys
import tempfile

import pytest
import resilient_sdk.app as app
from resilient_sdk.util import constants
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util import sdk_helpers, sdk_validate_configs
from tests.shared_mock_data import mock_paths

import keyring

# Set the logging to DEBUG for tests
LOG = logging.getLogger(constants.LOGGER_NAME)
LOG.setLevel(logging.DEBUG)


def _mk_temp_dir(dir_path=mock_paths.TEST_TEMP_DIR):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

    os.makedirs(dir_path)


def _rm_temp_dir(dir_path=mock_paths.TEST_TEMP_DIR):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)


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

def _mk_app_config_with_keyring():
    write_path = os.path.join(mock_paths.TEST_TEMP_DIR, "app.config")
    resilient_mock = "{0}.{1}".format(os.path.join(mock_paths.SHARED_MOCK_DATA_DIR, "resilient_api_mock"), "ResilientAPIMock")

    app_configs = """
[resilient]
#api_key_id=xxx
#api_key_secret=xxx

host=^host
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

    keyring.set_password("_", "host", "192.168.56.1")

    sdk_helpers.write_file(write_path, app_configs)

    return write_path, app_configs


def _add_to_cmd_line_args(args_to_add):
    sys.argv.extend(args_to_add)
    return sys.argv


def _pip_install(package):
    """
    pip installs given package
    """

    # should always upgrade pip
    install_cmd = ["pip", "install", "--upgrade", "pip"]
    sdk_helpers.run_subprocess(install_cmd)

    install_cmd = ["pip", "install", package]
    sdk_helpers.run_subprocess(install_cmd)

def _pip_uninstall(package):
    """
    pip uninstalls package
    """
    unisntall_cmd = ["pip", "uninstall", "-y", package]
    sdk_helpers.run_subprocess(unisntall_cmd)


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
def fx_mk_os_tmp_dir():
    tmp_dir = tempfile.gettempdir()
    sdk_tmp_dir_name = constants.SDK_RESOURCE_NAME
    dir_path = os.path.join(tmp_dir, sdk_tmp_dir_name)

    _mk_temp_dir(dir_path=dir_path)
    yield dir_path
    _rm_temp_dir(dir_path=dir_path)


@pytest.fixture
def fx_mk_app_config():
    """
    Before: Writes the app_configs text to an app.config file in the TEST_TEMP_DIR
    After: Nothing (mk_temp_dir will clean up)
    Note: MUST be called AFTER mk_temp_dir
    """
    return _mk_app_config()

@pytest.fixture
def fx_mk_app_config_with_keyring():
    """
    Before: Writes the app_configs with keyring used to an app.config file in the TEST_TEMP_DIR
    After: Nothing (mk_temp_dir will clean up)
    Note: MUST be called AFTER mk_temp_dir
    """
    return _mk_app_config_with_keyring()


@pytest.fixture(scope="module")
def fx_get_package_files_config():
    """
    Before: Maps the name of an attribute to its index, so that the attr_dict can be accessed in tests
    After: Nothing (there is nothing to clean up)
    """
    d = {}
    for i, (filename,_) in enumerate(sdk_validate_configs.package_files):
        d[filename] = i

    return d


@pytest.fixture
def fx_copy_fn_main_mock_integration():
    """
    Before: Creates temp dir and copies fn_main_mock_integration to it
    Returns a tuple (mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME, path_fn_main_mock_integration)
    After: Removes the temp directory
    """
    _mk_temp_dir()
    path_fn_main_mock_integration = os.path.join(mock_paths.TEST_TEMP_DIR, mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME)
    shutil.copytree(mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION, path_fn_main_mock_integration)
    yield (mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME, path_fn_main_mock_integration)
    _rm_temp_dir()


@pytest.fixture
def fx_copy_fn_main_mock_integration_w_playbooks():
    """
    Before: Creates temp dir and copies fn_main_mock_integration to it,
            then replaces the customize.py and data/export.res files to contain a playbook
    Returns a tuple (mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME, path_fn_main_mock_integration)
    After: Removes the temp directory
    """

    _mk_temp_dir()
    old_version = constants.CURRENT_SOAR_SERVER_VERSION
    constants.CURRENT_SOAR_SERVER_VERSION = None
    path_fn_main_mock_integration = os.path.join(mock_paths.TEST_TEMP_DIR, mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME)
    shutil.copytree(mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION, path_fn_main_mock_integration)
    shutil.copyfile(mock_paths.MOCK_CUSTOMIZE_PY_W_PLAYBOOK, os.path.join(path_fn_main_mock_integration, mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME, package_helpers.PATH_CUSTOMIZE_PY))
    shutil.copyfile(mock_paths.MOCK_EXPORT_RES_W_PLAYBOOK, os.path.join(path_fn_main_mock_integration, mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME, package_helpers.PATH_UTIL_DATA_DIR, package_helpers.BASE_NAME_LOCAL_EXPORT_RES))
    yield (mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME, path_fn_main_mock_integration)
    constants.CURRENT_SOAR_SERVER_VERSION = old_version
    _rm_temp_dir()


@pytest.fixture
def fx_copy_and_pip_install_fn_main_mock_integration():
    """
    Before: Creates temp dir and copies fn_main_mock_integration to it AND pip installs it
    Returns a tuple (mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME, path_fn_main_mock_integration)
    After: Removes the temp directory AND pip uninstalls it
    """
    _mk_temp_dir()
    path_fn_main_mock_integration = os.path.join(mock_paths.TEST_TEMP_DIR, mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME)
    shutil.copytree(mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION, path_fn_main_mock_integration)

    _pip_install(path_fn_main_mock_integration)

    yield (mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME, path_fn_main_mock_integration)

    _pip_uninstall(mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME)

    _rm_temp_dir()

@pytest.fixture
def fx_pip_install_tox():
    """
    Before: if tox not already installed: pip installs tox
    After: if tox wasn't already installed: pip uninstalls tox
    """

    # bool values of whether tox was already installed
    tox_installed = False
    if sdk_helpers.get_package_version(constants.TOX_PACKAGE_NAME):
        tox_installed = True

    if not tox_installed:
        _pip_install(constants.TOX_PACKAGE_NAME)

    yield

    if not tox_installed:
        _pip_uninstall(constants.TOX_PACKAGE_NAME)

@pytest.fixture
def fx_pip_install_pylint():
    """
    Before: if pylint not already installed: pip installs pylint
    After: if pylint wasn't already installed: pip uninstalls pylint
    """

    # bool values of whether pylint was already installed
    pylint_installed = False
    if sdk_helpers.get_package_version(constants.PYLINT_PACKAGE_NAME):
        pylint_installed = True

    if not pylint_installed:
        _pip_install(constants.PYLINT_PACKAGE_NAME)

    yield

    if not pylint_installed:
        _pip_uninstall(constants.PYLINT_PACKAGE_NAME)

@pytest.fixture
def fx_pip_install_bandit():
    """
    Before: if bandit not already installed: pip installs bandit
    After: if bandit wasn't already installed: pip uninstalls bandit
    """
    # TODO: once we support Python > 3.6 address this
    FIXED_VERSION = "1.7.1"

    # bool values of whether bandit was already installed
    bandit_installed = False
    if sdk_helpers.get_package_version(constants.BANDIT_PACKAGE_NAME):
        bandit_installed = True

    if not bandit_installed:
        _pip_install("{0}=={1}".format(constants.BANDIT_PACKAGE_NAME, FIXED_VERSION))

    yield

    if not bandit_installed:
        _pip_uninstall("{0}=={1}".format(constants.BANDIT_PACKAGE_NAME, FIXED_VERSION))


@pytest.fixture
def fx_cmd_line_args_codegen_base():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "codegen",
        "-p", mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME
    ]

    _add_to_cmd_line_args(args_to_add)

    yield

    sys.argv = original_cmd_line


@pytest.fixture
def fx_cmd_line_args_codegen_package():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "codegen",
        "-p", mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME,
        "-m", mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME,
        "-f", "mock_function_one",
        "--rule", "Mock Manual Rule", "Mock: Auto Rule", "Mock Task Rule", "Mock Script Rule", "Mock Manual Rule Message Destination",
        "--workflow", "mock_workflow_one", "mock_workflow_two",
        "--field", "mock_field_number", "mock_field_number", "mock_field_text_area",
        "--artifacttype", "mock_artifact_2", "mock_artifact_type_one",
        "--datatable", "mock_data_table",
        "--task", "mock_custom_task_one", "mock_cusom_task__________two",
        "--script", "Mock Script One",
        "--incidenttype", "mock_incidenttype_Āā", "mock incident type one",
    ]

    _add_to_cmd_line_args(args_to_add)

    yield

    sys.argv = original_cmd_line


@pytest.fixture
def fx_cmd_line_args_codegen_reload():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "codegen",
        "-p", mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME,
        "--reload",
        "--rule", "Additional Mock Rule"
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
        "-p", mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME
    ]

    _add_to_cmd_line_args(args_to_add)

    yield

    sys.argv = original_cmd_line


@pytest.fixture
def fx_cmd_line_args_validate():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "validate",
        "-p", mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME
    ]

    _add_to_cmd_line_args(args_to_add)

    yield

    sys.argv = original_cmd_line

@pytest.fixture
def fx_cmd_line_args_init():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "init"
    ]

    _add_to_cmd_line_args(args_to_add)

    yield

    sys.argv = original_cmd_line


@pytest.fixture
def fx_reset_argv():
    """
    Before: Takes a copy of sys.argv and allows functions to add args to it
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    yield

    sys.argv = original_cmd_line


@pytest.fixture
def fx_mock_settings_file_path():
    """
    Before: Change the settings file path to point to the test temp directory
    After: Change the settings file path back to the original value
    """
    old_sdk_settings_path = constants.SDK_SETTINGS_FILE_PATH
    constants.SDK_SETTINGS_FILE_PATH = "{}/test_settings.json".format(mock_paths.TEST_TEMP_DIR)

    yield

    constants.SDK_SETTINGS_FILE_PATH = old_sdk_settings_path

@pytest.fixture
def fx_create_mock_settings_file():
    """
    Before: Create a temporary file with the default settings file name
    """
    fake_settings_json = "{}/test_settings.json".format(mock_paths.TEST_TEMP_DIR)
    with open(fake_settings_json, "w") as f:
        pass

    yield

@pytest.fixture
def fx_cmd_line_args_docgen():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "docgen",
        "-p", mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME,
    ]

    args = _add_to_cmd_line_args(args_to_add)

    yield args

    sys.argv = original_cmd_line

@pytest.fixture
def fx_cmd_line_args_docgen_export_file():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "docgen",
        "-e", mock_paths.MOCK_EXPORT_RES, mock_paths.MOCK_PYTEST_XML_REPORT_PATH
    ]

    args = _add_to_cmd_line_args(args_to_add)

    yield args

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
        "-m", mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME,
        "-f", "mock_function_one",
        "--rule", "Mock Manual Rule", "Mock: Auto Rule", "Mock Task Rule", "Mock Script Rule", "Mock Manual Rule Message Destination",
        "-pre", "v2"
    ]

    _add_to_cmd_line_args(args_to_add)

    yield

    sys.argv = original_cmd_line


@pytest.fixture
def fx_cmd_line_args_clone_playbook_draft():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "clone",
        "-pb", "mock_main_pb", "new_pb_test",
        "--draft-playbook"
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
        "-p", mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME,
        "--set-version", "35.0.0"
    ]

    _add_to_cmd_line_args(args_to_add)

    yield

    sys.argv = original_cmd_line


@pytest.fixture
def fx_cmd_line_args_dev_set_version_51():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "dev",
        "-p", mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME,
        "--set-version", "51.0.0.0.0"
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
        "-p", mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME,
        "--set-version", "35.x.0"
    ]

    _add_to_cmd_line_args(args_to_add)

    yield

    sys.argv = original_cmd_line

@pytest.fixture
def fx_cmd_line_args_dev_set_bad_version_51():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "dev",
        "-p", mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME,
        "--set-version", "51.0.0"
    ]

    _add_to_cmd_line_args(args_to_add)

    yield

    sys.argv = original_cmd_line


@pytest.fixture
def fx_cmd_line_args_extract():
    """
    Before: adds args_to_add to cmd line so can be accessed by ArgParsers
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    args_to_add = [
        "extract",
        "--rule",
        "Mock Script Rule"
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


@pytest.fixture
def fx_add_dev_env_var():
    """
    Before: sets RES_SDK_DEV=1
    After: sets RES_SDK_DEV=0
    """
    os.environ[constants.ENV_VAR_DEV] = "1"

    yield

    os.environ[constants.ENV_VAR_DEV] = "0"
