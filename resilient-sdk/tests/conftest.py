#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

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

import pytest
import os
import shutil
from resilient_sdk.util.helpers import write_file, get_resilient_client
from tests.shared_mock_data import mock_paths


def _mk_temp_dir():
    if os.path.exists(mock_paths.TEST_TEMP_DIR):
        shutil.rmtree(mock_paths.TEST_TEMP_DIR)

    os.makedirs(mock_paths.TEST_TEMP_DIR)


def _rm_temp_dir():
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

    write_file(write_path, app_configs)

    return write_path


@pytest.fixture(scope="session")
def fx_mock_res_client():
    """
    Before: Creates a mock instance of res_client
    After: Removes temp directory used to store temp app.config
    """
    _mk_temp_dir()
    app_config = _mk_app_config()

    yield get_resilient_client(path_config_file=app_config)
    _rm_temp_dir()


@pytest.fixture
def fx_mk_temp_dir():
    """
    Before: Creates a directory at mock_paths.TEST_TEMP_DIR
    After: Removes the directory
    """
    _mk_temp_dir()
    yield fx_mk_temp_dir
    _rm_temp_dir()


@pytest.fixture
def fx_mk_app_config():
    """
    Before: Writes the app_configs text to an app.config file in the TEST_TEMP_DIR
    After: Nothing (mk_temp_dir will clean up)
    Note: MUST be called AFTER mk_temp_dir
    """
    return _mk_app_config()
