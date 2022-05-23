#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.

import os

import pkg_resources

PACKAGE_NAME = "resilient-circuits"

PASSWD_PATTERNS = ['pass', 'secret', 'pin', 'key', 'id']

INBOUND_MSG_DEST_PREFIX = "inbound_destinations"

APP_FUNCTION_PAYLOAD_VERSION = 2.0

MAX_NUM_WORKERS = 500
DEFAULT_SELFTEST_TIMEOUT_VALUE = 10

APP_LOG_DIR = os.environ.get("APP_LOG_DIR", "logs")
CMDS_LOGGER_NAME = "resilient_circuits_cmd_logger"
LOG_DIVIDER = "\n------------------------\n"

DEFAULT_NONE_STR = "Not found"
DEFAULT_UNKNOWN_STR = "Unknown"
ERROR_CA_FILE_NOT_FOUND = "Could not find a suitable TLS CA certificate bundle"
ERROR_USR_NOT_MEMBER_ORG = "The user is not a member of the specified organization"
ERROR_INVALID_USR = "Invalid user name or password"

# Selftest
SELFTEST_SUCCESS_STATE = "success"
SELFTEST_FAILURE_STATE = "failure"
SELFTEST_UNIMPLEMENTED_STATE = "unimplemented"

# app configs
INBOUND_MSG_APP_CONFIG_Q_NAME = "inbound_destination_api_name"
APP_CONFIG_TRAP_EXCEPTION = "trap_exception"
APP_CONFIG_SELFTEST_TIMEOUT = "selftest_timeout"

# Headers
HEADER_CIRCUITS_VER_KEY = "Resilient-Circuits-Version"
HEADER_CIRCUITS_VER_VALUE = pkg_resources.get_distribution(PACKAGE_NAME).version
