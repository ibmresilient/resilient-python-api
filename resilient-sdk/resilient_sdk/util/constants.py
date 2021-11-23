#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.
import os

LOGGER_NAME = "resilient_sdk_log"
LOG_DIVIDER = "\n------------------------\n"
ENV_VAR_DEV = "RES_SDK_DEV"
ENV_VAR_APP_CONFIG_FILE = "APP_CONFIG_FILE"

RESILIENT_LIBRARIES_VERSION = "43.0.0"
RESILIENT_LIBRARIES_VERSION_DEV = "43.0.0"
RESILIENT_VERSION_WITH_PROXY_SUPPORT = (42, 0, 0)
CURRENT_SOAR_SERVER_VERSION = 42

MIN_SUPPORTED_PY_VERSION = (3, 6)
SDK_PACKAGE_NAME = "resilient-sdk"
CIRCUITS_PACKAGE_NAME = "resilient-circuits"

SUB_CMD_PACKAGE = ("--package", "-p")
SUB_CMD_SDK_SETTINGS = ("--settings", )

# file for SDK settings
SDK_SETTINGS_PARSER_NAME = "sdk_settings_file"
SDK_SETTINGS_FILENAME = ".sdk_settings.json"
SDK_SETTINGS_FILE_PATH = os.path.join(os.path.expanduser("~"), ".resilient", SDK_SETTINGS_FILENAME)

# Resilient export file suffix.
RES_EXPORT_SUFFIX = ".res"
# Endpoint url for importing a configuration
IMPORT_URL = "/configurations/imports"

# Path to package templates for jinja rendering
PACKAGE_TEMPLATE_PATH = os.path.join("data", "codegen", "templates", "package_template")
DOCGEN_TEMPLATE_PATH = os.path.join("data", "docgen", "templates")
VALIDATE_TEMPLATE_PATH = os.path.join("data", "validate", "templates")
VALIDATE_REPORT_TEMPLATE_NAME = "validate_report.md.jinja2"

# tox tests constants (used in validate)
TOX_PACKAGE_NAME = "tox"
TOX_INI_FILENAME = "tox.ini"
TOX_TEMP_PATH_XML_REPORT = ".validate_tmp_dir"
TOX_TESTS_DEFAULT_ARGS = ['--resilient_email', '"integrations@example.org"', '--resilient_password', '"supersecret"', '--resilient_host', '"example.com"', '--resilient_org', '"Test Organization"']


DOCGEN_PLACEHOLDER_STRING = "::CHANGE_ME::"

VALIDATE_LOG_LEVEL_CRITICAL = "CRITICAL"
VALIDATE_LOG_LEVEL_ERROR = VALIDATE_LOG_LEVEL_CRITICAL
VALIDATE_LOG_LEVEL_WARNING = "WARNING"
VALIDATE_LOG_LEVEL_INFO = "INFO"
VALIDATE_LOG_LEVEL_DEBUG = "DEBUG"
