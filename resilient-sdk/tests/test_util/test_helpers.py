#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

import os
import stat
import pytest
import jinja2
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util import helpers
from tests.shared_mock_data import mock_data, mock_paths


def test_get_resilient_client():
    # TODO:
    pass


def test_setup_jinja_env():
    jinja_env = helpers.setup_jinja_env(mock_paths.TEST_TEMP_DIR)
    assert isinstance(jinja_env, jinja2.Environment)
    assert jinja_env.loader.package_path == mock_paths.TEST_TEMP_DIR


def test_write_file(mk_temp_dir):
    temp_file = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_file.txt")
    helpers.write_file(temp_file, mock_data.mock_file_contents)
    assert os.path.isfile(temp_file)


def test_is_valid_package_name():
    assert helpers.is_valid_package_name("fn_mock_integration") is True
    assert helpers.is_valid_package_name("fnmockintegration") is True
    assert helpers.is_valid_package_name("get") is False
    assert helpers.is_valid_package_name("$%&(#)@*$") is False
    assert helpers.is_valid_package_name("fn-mock-integration") is False
    assert helpers.is_valid_package_name("fn-ځ ڂ ڃ ڄ څ-integration") is False


def test_has_permissions(mk_temp_dir):
    temp_permissions_file = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_permissions.txt")
    helpers.write_file(temp_permissions_file, mock_data.mock_file_contents)

    # Set permissions to Read only
    os.chmod(temp_permissions_file, stat.S_IRUSR)

    with pytest.raises(SDKException, match=r"User does not have WRITE permissions"):
        helpers.has_permissions(os.W_OK, temp_permissions_file)

    # Set permissions to Write only
    os.chmod(temp_permissions_file, stat.S_IWUSR)

    with pytest.raises(SDKException, match=r"User does not have READ permissions"):
        helpers.has_permissions(os.R_OK, temp_permissions_file)


def test_validate_file_paths(mk_temp_dir):
    non_exist_file = "/non_exits/path/non_exist_file.txt"
    with pytest.raises(SDKException, match=r"Could not find file: " + non_exist_file):
        helpers.validate_file_paths(None, non_exist_file)

    exists_file = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_existing_file.txt")
    helpers.write_file(exists_file, mock_data.mock_file_contents)

    helpers.validate_file_paths(None, exists_file)


def test_validate_dir_paths(mk_temp_dir):
    non_exist_dir = "/non_exits/path/"
    with pytest.raises(SDKException, match=r"Could not find directory: " + non_exist_dir):
        helpers.validate_dir_paths(None, non_exist_dir)

    exists_dir = mock_paths.TEST_TEMP_DIR

    helpers.validate_dir_paths(None, exists_dir)


def test_get_latest_org_export():
    # TODO: this be tricky, mock response?
    pass


def test_get_obj_from_list():
    # TODO:
    pass


def test_get_res_obj():
    # TODO:
    pass


def test_get_from_export():
    # TODO:
    pass


def test_minify_export():
    # TODO:
    pass