#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

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

import sys
import os
import shutil
import pytest
from tests.shared_mock_data import mock_paths
from resilient import constants


def _mk_temp_dir():
    if os.path.exists(mock_paths.TEST_TEMP_DIR):
        shutil.rmtree(mock_paths.TEST_TEMP_DIR)

    os.makedirs(mock_paths.TEST_TEMP_DIR)


def _rm_temp_dir():
    if os.path.exists(mock_paths.TEST_TEMP_DIR):
        shutil.rmtree(mock_paths.TEST_TEMP_DIR)


def _add_to_cmd_line_args(args_to_add):
    sys.argv.extend(args_to_add)


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
def fx_add_proxy_env_var():
    """
    Before: set HTTPS_PROXY, HTTP_PROXY and NO_PROXY
    After: unset HTTPS_PROXY, HTTP_PROXY and NO_PROXY
    """
    os.environ[constants.ENV_HTTPS_PROXY] = "https://192.168.0.5:3128"
    os.environ[constants.ENV_HTTP_PROXY] = "http://192.168.0.5:3128"
    os.environ[constants.ENV_NO_PROXY] = "subdomain.example.com,192.168.1.5,.example.com"

    yield

    os.environ[constants.ENV_HTTPS_PROXY] = ""
    os.environ[constants.ENV_HTTP_PROXY] = ""
    os.environ[constants.ENV_NO_PROXY] = ""


@pytest.fixture
def fx_add_proxy_env_var_with_user():
    """
    Before: set HTTPS_PROXY, HTTP_PROXY and NO_PROXY
    After: unset HTTPS_PROXY, HTTP_PROXY and NO_PROXY
    """
    os.environ[constants.ENV_HTTPS_PROXY] = "https://mockusername:mockpw1234567890%21%40%23%24%25%5E%26%2A%28%29-%2B_%3D%5B%5D%7B%3B%27%5C%7D%3A%22%2F%7C%2C%3C%3E%3F%60%7E@192.168.0.5:3128"
    os.environ[constants.ENV_HTTP_PROXY] = "http://mockusername:mockpw1234567890%21%40%40%40%40%23%24%25%5E%26%2A%28%29-%2B_%3D%5B%5D%7B%3B%27%5C%7D%3A%22%2F%7C%2C%3C%3E%3F%60%7E@192.168.0.5:3128"
    os.environ[constants.ENV_NO_PROXY] = "subdomain.example.com,192.168.1.5,.example.com"

    yield

    os.environ[constants.ENV_HTTPS_PROXY] = ""
    os.environ[constants.ENV_HTTP_PROXY] = ""
    os.environ[constants.ENV_NO_PROXY] = ""
