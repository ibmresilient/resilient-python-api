#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

"""Common paths used in tests"""

import os

SHARED_MOCK_DATA_DIR = os.path.dirname(os.path.realpath(__file__))
TESTS_DIR = os.path.dirname(SHARED_MOCK_DATA_DIR)
RESILIENT_API_DATA = os.path.join(SHARED_MOCK_DATA_DIR, "resilient_api_data")

PATH_SDK_SETUP_PY = os.path.abspath(os.path.join(TESTS_DIR, "..", "setup.py"))

TEST_TEMP_DIR = os.path.join(TESTS_DIR, "test_temp")

MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME = "fn_main_mock_integration"

MOCK_SDK_SETTINGS_PATH = os.path.join(SHARED_MOCK_DATA_DIR, ".mock_sdk_settings.json")
MOCK_APP_LOG_PATH = os.path.join(SHARED_MOCK_DATA_DIR, "mock_app.log")

MOCK_PACKAGE_FILES_DIR = os.path.join(SHARED_MOCK_DATA_DIR, "mock_package_files")
MOCK_SETUP_PY = os.path.join(MOCK_PACKAGE_FILES_DIR, "setup.py")
MOCK_SETUP_PY_LINES = os.path.join(MOCK_PACKAGE_FILES_DIR, "setup_py_lines.py")
MOCK_SETUP_CALLABLE = os.path.join(MOCK_PACKAGE_FILES_DIR, "setup_callable_data.txt")
MOCK_CONFIG_PY = os.path.join(MOCK_PACKAGE_FILES_DIR, "config.py")
MOCK_CUSTOMIZE_PY = os.path.join(MOCK_PACKAGE_FILES_DIR, "customize.py")
MOCK_OLD_CUSTOMIZE_PY = os.path.join(MOCK_PACKAGE_FILES_DIR, "customize_old.py")
MOCK_CUSTOMIZE_PY_W_PLAYBOOK = os.path.join(MOCK_PACKAGE_FILES_DIR, "mock_customize_w_playbook.py")

MOCK_EXPORT_RES = os.path.join(SHARED_MOCK_DATA_DIR, "mock_export.res")
MOCK_EXPORT_RES_CORRUPT = os.path.join(SHARED_MOCK_DATA_DIR, "mock_export_corrupt.res")
MOCK_EXPORT_RES_W_PLAYBOOK = os.path.join(MOCK_PACKAGE_FILES_DIR, "mock_export_w_playbook.res")
MOCK_EXPORT_RES_W_PLAYBOOK_W_SCRIPTS = os.path.join(MOCK_PACKAGE_FILES_DIR, "mock_export_w_playbook_w_scripts.res")
MOCK_RELOAD_EXPORT_RES_W_PLAYBOOK = os.path.join(MOCK_PACKAGE_FILES_DIR, "mock_reload_export_w_playbook.res")
MOCK_RELOAD_EXPORT_RES = os.path.join(SHARED_MOCK_DATA_DIR, "mock_reload_export.res")
MOCK_ZIP = os.path.join(SHARED_MOCK_DATA_DIR, "mock.zip")
MOCK_EXPORT_RESZ = os.path.join(SHARED_MOCK_DATA_DIR, "mock_export.resz")

MOCK_INT_DIR = os.path.join(MOCK_PACKAGE_FILES_DIR, "mock_integrations")
MOCK_INT_FN_MAIN_MOCK_INTEGRATION = os.path.join(MOCK_INT_DIR, MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME)
MOCK_INT_FN_MAIN_MOCK_INTEGRATION_UTIL = os.path.join(MOCK_INT_FN_MAIN_MOCK_INTEGRATION, MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME, "util")

MOCK_DOCKERFILE_PATH = os.path.join(MOCK_INT_DIR, "fn_main_mock_integration/Dockerfile")

MOCK_APP_ZIP_FILES_DIR = os.path.join(MOCK_PACKAGE_FILES_DIR, "mock_app_zip_files")
MOCK_APP_ZIP_APP_JSON = os.path.join(MOCK_APP_ZIP_FILES_DIR, "mock_app.json")
MOCK_APP_ZIP_EXPORT_RES = os.path.join(MOCK_APP_ZIP_FILES_DIR, "mock_export.res")
MOCK_APP_ZIP_EXPORT_RES_WITH_PAYLOAD_SAMPLES = os.path.join(MOCK_APP_ZIP_FILES_DIR, "mock_with_payload_samples_export.res")

MOCK_PYTEST_XML_REPORT_PATH = os.path.join(SHARED_MOCK_DATA_DIR, "mock_xml_test_report.xml")
