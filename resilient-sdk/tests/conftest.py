#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

"""
This is where we can write shared pytest fixtures

Note: code after the 'yield' statement in a fixture
is ran after the test has complete
"""

import pytest
import os
import shutil
from tests.shared_mock_data import mock_paths


@pytest.fixture
def mk_temp_dir():
    """
    Before: Creates a directory at mock_paths.TEST_TEMP_DIR
    After: Removes the directory
    """
    if os.path.exists(mock_paths.TEST_TEMP_DIR):
        shutil.rmtree(mock_paths.TEST_TEMP_DIR)

    os.makedirs(mock_paths.TEST_TEMP_DIR)

    yield mk_temp_dir

    shutil.rmtree(mock_paths.TEST_TEMP_DIR)
