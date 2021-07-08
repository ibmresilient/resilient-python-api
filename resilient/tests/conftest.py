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
    os.environ[constants.ENV_HTTPS_PROXY] = "https://mock.example.com:3128"
    os.environ[constants.ENV_HTTP_PROXY] = "http://mock.example.com:3128"
    os.environ[constants.ENV_NO_PROXY] = "example.com"

    yield

    os.environ[constants.ENV_HTTPS_PROXY] = ""
    os.environ[constants.ENV_HTTP_PROXY] = ""
    os.environ[constants.ENV_NO_PROXY] = ""
