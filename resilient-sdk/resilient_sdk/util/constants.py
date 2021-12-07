#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.
import os

import pkg_resources

PATH_RES_DEFAULT_DIR = os.path.abspath(os.path.join(os.path.expanduser("~"), ".resilient"))
PATH_RES_DEFAULT_LOG_DIR = os.path.join(PATH_RES_DEFAULT_DIR, "logs")
PATH_RES_DEFAULT_LOG_FILE = os.path.join(PATH_RES_DEFAULT_LOG_DIR, "app.log")

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
SDK_RESOURCE_NAME = "resilient_sdk"
CIRCUITS_PACKAGE_NAME = "resilient-circuits"

SUB_CMD_OPT_PACKAGE = ("--package", "-p")
SUB_CMD_OPT_SDK_SETTINGS = ("--settings", )

# file for SDK settings
SDK_SETTINGS_PARSER_NAME = "sdk_settings_file"
SDK_SETTINGS_FILENAME = ".sdk_settings.json"
SDK_SETTINGS_FILE_PATH = os.path.join(PATH_RES_DEFAULT_DIR, SDK_SETTINGS_FILENAME)

# Resilient export file suffix.
RES_EXPORT_SUFFIX = ".res"
# Endpoint url for importing a configuration
IMPORT_URL = "/configurations/imports"

# Path to package templates for jinja rendering
PACKAGE_TEMPLATE_PATH = os.path.join("data", "codegen", "templates", "package_template")
PACKAGE_TEMPLATE_PACKAGE_DIR = os.path.join(PACKAGE_TEMPLATE_PATH, "package")
DOCGEN_TEMPLATE_PATH = os.path.join("data", "docgen", "templates")
BASE_PATH_VALIDATE_DATA = os.path.join("data", "validate")
VALIDATE_TEMPLATE_PATH = os.path.join(BASE_PATH_VALIDATE_DATA, "templates")
VALIDATE_REPORT_TEMPLATE_NAME = "validate_report.md.jinja2"

# tox tests constants (used in validate)
TOX_PACKAGE_NAME = "tox"
TOX_INI_FILENAME = "tox.ini"
TOX_TEMP_PATH_XML_REPORT = ".validate_tmp_dir"
TOX_TESTS_DEFAULT_ARGS = ['--resilient_email', '"integrations@example.org"', '--resilient_password', '"supersecret"', '--resilient_host', '"example.com"', '--resilient_org', '"Test Organization"']
TOX_MIN_ENV_VERSION = "py36" # the last character here must be a number and will be used as the base value for checks of envlist
TOX_MIN_PACKAGE_VERSION = (3, 24, 4)

# pylint constants (for validate)
PYLINT_PACKAGE_NAME = "pylint"
PATH_VALIDATE_PYLINT_RC_FILE = pkg_resources.resource_filename(SDK_RESOURCE_NAME, os.path.join(BASE_PATH_VALIDATE_DATA, ".pylintrc"))

ICON_APP_LOGO_REQUIRED_WIDTH = 200
ICON_APP_LOGO_REQUIRED_HEIGHT = 72
ICON_COMPANY_LOGO_REQUIRED_WIDTH = 100
ICON_COMPANY_LOGO_REQUIRED_HEIGHT = 100

DOCGEN_PLACEHOLDER_STRING = "::CHANGE_ME::"

VALIDATE_LOG_LEVEL_CRITICAL = "CRITICAL"
VALIDATE_LOG_LEVEL_ERROR = VALIDATE_LOG_LEVEL_CRITICAL
VALIDATE_LOG_LEVEL_WARNING = "WARNING"
VALIDATE_LOG_LEVEL_INFO = "INFO"
VALIDATE_LOG_LEVEL_DEBUG = "DEBUG"
