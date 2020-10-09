#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

"""Common paths used in tests"""

import os

SHARED_MOCK_DATA_DIR = os.path.dirname(os.path.realpath(__file__))
TESTS_DIR = os.path.dirname(SHARED_MOCK_DATA_DIR)
RESILIENT_API_DATA = os.path.join(SHARED_MOCK_DATA_DIR, "resilient_api_data")

TEST_TEMP_DIR = os.path.join(TESTS_DIR, "test_temp")

MOCK_PACKAGE_FILES_DIR = os.path.join(SHARED_MOCK_DATA_DIR, "mock_package_files")
MOCK_SETUP_PY = os.path.join(MOCK_PACKAGE_FILES_DIR, "setup.py")
MOCK_SETUP_PY_LINES = os.path.join(MOCK_PACKAGE_FILES_DIR, "setup_py_lines.py")
MOCK_SETUP_CALLABLE = os.path.join(MOCK_PACKAGE_FILES_DIR, "setup_callable_data.txt")
MOCK_CONFIG_PY = os.path.join(MOCK_PACKAGE_FILES_DIR, "config.py")
MOCK_CUSTOMIZE_PY = os.path.join(MOCK_PACKAGE_FILES_DIR, "customize.py")
MOCK_OLD_CUSTOMIZE_PY = os.path.join(MOCK_PACKAGE_FILES_DIR, "customize_old.py")

MOCK_EXPORT_RES = os.path.join(SHARED_MOCK_DATA_DIR, "mock_export.res")
MOCK_ZIP = os.path.join(SHARED_MOCK_DATA_DIR, "mock.zip")
MOCK_EXPORT_RESZ = os.path.join(SHARED_MOCK_DATA_DIR, "mock_export.resz")

MOCK_INT_DIR = os.path.join(MOCK_PACKAGE_FILES_DIR, "mock_integrations")
MOCK_INT_FN_MAIN_MOCK_INTEGRATION = os.path.join(MOCK_INT_DIR, "fn_main_mock_integration")
