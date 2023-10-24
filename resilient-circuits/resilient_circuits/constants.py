#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import os

import pkg_resources

PACKAGE_NAME = "resilient-circuits"

# list compiled from ideas in https://stackoverflow.com/a/43369417
PASSWORD_PATTERNS = ['token', 'pass', 'secret', 'pin', 'key', 'session', 'connection', 'jwt']

INBOUND_MSG_DEST_PREFIX = "inbound_destinations"

APP_FUNCTION_PAYLOAD_VERSION = 2.0

MIN_NUM_WORKERS = 1
MAX_NUM_WORKERS = 500
MIN_LOG_BYTES = 100000
MIN_BACKUP_COUNT = 0
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
APP_CONFIG_HEARTBEAT_TIMEOUT_THRESHOLD = "heartbeat_timeout_threshold"
APP_CONFIG_RC_USE_PERSISTENT_SESSIONS = "rc_use_persistent_sessions"
APP_CONFIG_LOG_MAX_BYTES = "log_max_bytes"
APP_CONFIG_LOG_BACKUP_COUNT = "log_backup_count"

# Headers
HEADER_CIRCUITS_VER_KEY = "Resilient-Circuits-Version"
HEADER_CIRCUITS_VER_VALUE = pkg_resources.get_distribution(PACKAGE_NAME).version

# Exit Codes
EXIT_SELFTEST_ERROR = 1             # Error running App's selftest
EXIT_SELFTEST_UNIMPLEMENTED = 2     # selftest was unimplemented
EXIT_REST_CONNECTION_ERROR = 20     # REST: Generic connection error
EXIT_REST_UNAUTHORIZED = 21         # REST: Connection unauthorized
EXIT_REST_OS_ERROR = 22             # REST: OSError (Could not find Certificate file)
EXIT_REST_SSL_ERROR = 23            # REST: SSL Error (Invalid Certificate Error)
EXIT_REST_ORG_ERROR = 24            # REST: Organization Membership Error
EXIT_REST_INVALID_PW = 25           # REST: Invalid Username or Password
EXIT_STOMP_ERROR = 30               # STOMP: Generic connection error
EXIT_STOMP_UNAUTHORIZED_CONN = 31   # STOMP: Not authorized to instansiate STOMP connection
EXIT_STOMP_UNAUTHORIZED_Q = 32      # STOMP: Not authorized to read from queue
EXIT_STOMP_Q_TIMEOUT = 33           # STOMP: Timed out trying to see if resilient-circuits is subscribed to a message destination
EXIT_STOMP_HEARTBEAT_TIMEOUT = 34   # STOMP: The delta of the current HeartbeatTimeout event and the first HeartbeatTimeout event is greater than the 'heartbeat_timeout_threshold'

# STOMP connection constants
STOMP_MAX_CONNECTION_ERRORS = 1     # default number of errors when heartbeat is lost